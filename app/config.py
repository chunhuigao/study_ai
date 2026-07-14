from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
STATIC_DIR = BASE_DIR / "static"

COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "pdf_documents")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "160"))
TOP_K = int(os.getenv("TOP_K", "6"))

OCR_LANGUAGE = os.getenv("OCR_LANGUAGE", "eng+chi_sim")
OCR_DPI = int(os.getenv("OCR_DPI", "220"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD")
MIN_TEXT_CHARS_PER_PAGE = int(os.getenv("MIN_TEXT_CHARS_PER_PAGE", "80"))
