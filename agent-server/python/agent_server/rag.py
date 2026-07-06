import hashlib
import json
import re
from datetime import datetime
from pathlib import Path


SERVER_DIR = Path(__file__).resolve().parents[2]
RAG_DIR = SERVER_DIR / "var" / "rag"
INDEX_FILE = RAG_DIR / "index.json"


def _load_index():
    if not INDEX_FILE.exists():
        return {"documents": [], "chunks": []}
    try:
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"documents": [], "chunks": []}


def _save_index(index):
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _document_id(path: Path):
    stat = path.stat()
    raw = f"{path.resolve()}:{stat.st_size}:{int(stat.st_mtime)}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _clean_text(text):
    # PDF 抽出来的文本经常有多余空格和空行，先压平，方便后续切块和检索。
    text = re.sub(r"[ \t]+", " ", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_text(text, chunk_size=900, overlap=120):
    """把长文本切成重叠小块。

    RAG 检索的基本单位通常不是整篇文档，而是 chunk。加一点 overlap 可以避免
    答案刚好跨越两个 chunk 时被切断。
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return [item for item in chunks if item]


def _tokenize(text):
    # 中文按单字，英文按词。这个实现很朴素，但足够展示“检索”的核心机制。
    return re.findall(r"[\u4e00-\u9fff]|[A-Za-z0-9_]+", (text or "").lower())


def _score_chunk(question_terms, chunk):
    if not question_terms:
        return 0
    chunk_terms = _tokenize(chunk["text"])
    if not chunk_terms:
        return 0

    frequencies = {}
    for term in chunk_terms:
        frequencies[term] = frequencies.get(term, 0) + 1

    score = 0
    for term in question_terms:
        score += frequencies.get(term, 0)
    return score


def _require_pypdf():
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("缺少 PDF 解析依赖，请先运行：python3 -m pip install pypdf") from error
    return PdfReader


def ingest_pdf(file_path):
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError("当前学习版 RAG 只支持 PDF 文件")

    PdfReader = _require_pypdf()
    reader = PdfReader(str(path))
    doc_id = _document_id(path)
    page_count = len(reader.pages)
    new_chunks = []

    for page_index, page in enumerate(reader.pages, start=1):
        page_text = _clean_text(page.extract_text() or "")
        for chunk_index, chunk_text in enumerate(_chunk_text(page_text), start=1):
            chunk_id = f"{doc_id}_p{page_index}_c{chunk_index}"
            new_chunks.append(
                {
                    "id": chunk_id,
                    "documentId": doc_id,
                    "fileName": path.name,
                    "filePath": str(path),
                    "page": page_index,
                    "text": chunk_text,
                }
            )

    if not new_chunks:
        raise ValueError("没有从 PDF 中抽取到文本。扫描版 PDF 需要后续接 OCR。")

    index = _load_index()
    index["documents"] = [doc for doc in index["documents"] if doc["id"] != doc_id]
    index["chunks"] = [chunk for chunk in index["chunks"] if chunk["documentId"] != doc_id]
    index["documents"].append(
        {
            "id": doc_id,
            "fileName": path.name,
            "filePath": str(path),
            "pageCount": page_count,
            "chunkCount": len(new_chunks),
            "createdAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": "pdf",
        }
    )
    index["chunks"].extend(new_chunks)
    _save_index(index)

    return {
        "ok": True,
        "document": index["documents"][-1],
        "chunkCount": len(new_chunks),
    }


def list_documents():
    index = _load_index()
    return {
        "ok": True,
        "documents": index["documents"],
        "chunkCount": len(index["chunks"]),
    }


def clear_index():
    _save_index({"documents": [], "chunks": []})
    return {"ok": True, "documents": [], "chunkCount": 0}


def query(question, top_k=4):
    question = (question or "").strip()
    if not question:
        raise ValueError("请输入问题")

    index = _load_index()
    chunks = index["chunks"]
    if not chunks:
        return {
            "ok": True,
            "answer": "还没有可检索的资料。请先上传一个 PDF。",
            "sources": [],
        }

    question_terms = _tokenize(question)
    ranked = []
    for chunk in chunks:
        score = _score_chunk(question_terms, chunk)
        if score > 0:
            ranked.append((score, chunk))

    ranked.sort(key=lambda item: item[0], reverse=True)
    sources = [chunk for _score, chunk in ranked[:top_k]]

    if not sources:
        return {
            "ok": True,
            "answer": "我在已上传资料里没有检索到明显相关的片段，可以换个关键词试试。",
            "sources": [],
        }

    answer_lines = [
        "根据已上传 PDF，我检索到这些相关内容：",
        "",
    ]
    for index_no, source in enumerate(sources, start=1):
        snippet = source["text"][:260].replace("\n", " ")
        answer_lines.append(f"{index_no}. {snippet}")

    answer_lines.extend(
        [
            "",
            "学习提示：这是一版轻量 RAG，回答来自检索片段的摘取和整理；后续接入大模型后，可以把这些片段作为上下文生成更自然的答案。",
        ]
    )

    return {
        "ok": True,
        "answer": "\n".join(answer_lines),
        "sources": [
            {
                "id": source["id"],
                "fileName": source["fileName"],
                "page": source["page"],
                "text": source["text"],
            }
            for source in sources
        ],
    }

