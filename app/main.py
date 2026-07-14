from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import STATIC_DIR, TOP_K, UPLOAD_DIR
from .pdf_pipeline import chunk_pages, document_id_for, extract_pdf_pages, is_ocr_available
from .rag_store import RagStore


app = FastAPI(title="PDF RAG Chatbot")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
store = RagStore()


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    top_k: int = Field(default=TOP_K, ge=1, le=12)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/upload")
async def upload_pdf(file: Annotated[UploadFile, File()]) -> dict[str, object]:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="请上传 PDF 文件。")

    safe_name = Path(file.filename).name
    destination = UPLOAD_DIR / safe_name
    with destination.open("wb") as output:
        shutil.copyfileobj(file.file, output)

    try:
        document_id = document_id_for(destination)
        pages = extract_pdf_pages(destination)
        chunks = chunk_pages(pages, source_name=safe_name, document_id=document_id)
        store.add_chunks(chunks)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF 处理失败：{exc}") from exc

    return {
        "document_id": document_id,
        "filename": safe_name,
        "pages": len(pages),
        "chunks": len(chunks),
        "ocr_pages": sum(1 for page in pages if page.extraction == "ocr"),
        "text_pages": sum(1 for page in pages if page.extraction == "text"),
        "empty_pages": sum(1 for page in pages if page.extraction == "empty"),
        "ocr_available": is_ocr_available(),
        "warning": _upload_warning(pages, len(chunks)),
    }


@app.post("/api/chat")
def chat(request: ChatRequest) -> dict[str, object]:
    return store.answer(request.question, top_k=request.top_k)


@app.get("/api/stats")
def stats() -> dict[str, object]:
    return store.stats()


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def _upload_warning(pages: list[object], chunk_count: int) -> str | None:
    if chunk_count > 0:
        return None
    empty_pages = sum(1 for page in pages if getattr(page, "extraction", None) == "empty")
    if empty_pages and not is_ocr_available():
        return (
            "这个 PDF 没有可提取的文本层，且当前系统没有安装 Tesseract OCR，"
            "所以无法生成 chunks。安装 Tesseract 后重新上传即可处理扫描件。"
        )
    if empty_pages:
        return "这个 PDF 没有可提取的文本层，OCR 未识别出可用文本。"
    return "没有生成 chunks，请检查 PDF 内容是否为空或调整切块配置。"
