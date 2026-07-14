from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import asdict
from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection
from openai import OpenAI

from .config import CHAT_MODEL, CHROMA_DIR, COLLECTION_NAME, EMBEDDING_MODEL, TOP_K
from .pdf_pipeline import TextChunk


class Embeddings:
    def __init__(self) -> None:
        self.client = OpenAI() if os.getenv("OPENAI_API_KEY") else None

    def embed(self, texts: list[str]) -> list[list[float]]:
        if self.client:
            response = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            return [item.embedding for item in response.data]
        return [_hash_embedding(text) for text in texts]


class RagStore:
    def __init__(self) -> None:
        CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        self.collection: Collection = self.client.get_or_create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        self.embeddings = Embeddings()
        self.openai = OpenAI() if os.getenv("OPENAI_API_KEY") else None

    def add_chunks(self, chunks: list[TextChunk]) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=self.embeddings.embed([chunk.text for chunk in chunks]),
            metadatas=[chunk.metadata for chunk in chunks],
        )

    def search(self, question: str, top_k: int = TOP_K) -> list[dict[str, Any]]:
        results = self.collection.query(
            query_embeddings=self.embeddings.embed([question]),
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]
        ids = results.get("ids", [[]])[0]
        hits = []
        for hit_id, document, metadata, distance in zip(ids, documents, metadatas, distances):
            hits.append(
                {
                    "id": hit_id,
                    "text": document,
                    "metadata": metadata,
                    "score": 1 - float(distance),
                }
            )
        return hits

    def answer(self, question: str, top_k: int = TOP_K) -> dict[str, Any]:
        hits = self.search(question, top_k=top_k)
        if not hits:
            return {
                "answer": "当前知识库里还没有可召回的内容，请先上传 PDF。",
                "sources": [],
            }

        if not self.openai:
            context_answer = "\n\n".join(
                f"[{index}] {hit['text'][:700]}" for index, hit in enumerate(hits, start=1)
            )
            return {
                "answer": (
                    "未检测到 OPENAI_API_KEY，已返回最相关的原文片段：\n\n"
                    f"{context_answer}"
                ),
                "sources": _sources_from_hits(hits),
            }

        context = "\n\n".join(
            (
                f"[{index}] source={hit['metadata'].get('source')} "
                f"page={hit['metadata'].get('page')}\n{hit['text']}"
            )
            for index, hit in enumerate(hits, start=1)
        )
        response = self.openai.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是一个严谨的 PDF RAG 助手。只根据给定上下文回答。"
                        "如果上下文不足，说明无法从文档中确认。回答要简洁，并引用页码。"
                    ),
                },
                {
                    "role": "user",
                    "content": f"问题：{question}\n\n上下文：\n{context}",
                },
            ],
            temperature=0.2,
        )
        return {
            "answer": response.choices[0].message.content or "",
            "sources": _sources_from_hits(hits),
        }

    def stats(self) -> dict[str, Any]:
        count = self.collection.count()
        peek = self.collection.peek(limit=100)
        documents: dict[str, dict[str, Any]] = {}
        for metadata in peek.get("metadatas", []):
            if not metadata:
                continue
            document_id = str(metadata.get("document_id", "unknown"))
            document = documents.setdefault(
                document_id,
                {
                    "document_id": document_id,
                    "source": metadata.get("source", "unknown"),
                    "pages": set(),
                    "extractions": set(),
                },
            )
            document["pages"].add(metadata.get("page"))
            document["extractions"].add(metadata.get("extraction"))
        return {
            "chunks": count,
            "documents": [
                {
                    **{key: value for key, value in document.items() if key not in {"pages", "extractions"}},
                    "pages": len(document["pages"]),
                    "extractions": sorted(item for item in document["extractions"] if item),
                }
                for document in documents.values()
            ],
            "embedding": "openai" if self.embeddings.client else "local-hash",
            "chat": "openai" if self.openai else "extractive",
        }


def _hash_embedding(text: str, dimensions: int = 384) -> list[float]:
    vector = [0.0] * dimensions
    tokens = re.findall(r"[\w\u4e00-\u9fff]+", text.lower())
    if not tokens:
        return vector
    for token in tokens:
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dimensions
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _sources_from_hits(hits: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources = []
    for hit in hits:
        metadata = hit["metadata"] or {}
        sources.append(
            {
                "source": metadata.get("source"),
                "page": metadata.get("page"),
                "chunk": metadata.get("chunk"),
                "extraction": metadata.get("extraction"),
                "score": round(float(hit["score"]), 4),
                "preview": hit["text"][:260],
            }
        )
    return sources

