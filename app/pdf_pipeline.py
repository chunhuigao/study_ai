from __future__ import annotations

import hashlib
import io
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image

from .config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    MIN_TEXT_CHARS_PER_PAGE,
    OCR_DPI,
    OCR_LANGUAGE,
    TESSERACT_CMD,
)


@dataclass(frozen=True)
class PageText:
    page: int
    text: str
    extraction: str


@dataclass(frozen=True)
class TextChunk:
    id: str
    text: str
    metadata: dict[str, str | int]


def document_id_for(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.name.encode("utf-8"))
    digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def extract_pdf_pages(path: Path) -> list[PageText]:
    pages: list[PageText] = []
    ocr_ready = is_ocr_available()
    with fitz.open(path) as doc:
        for page_index, page in enumerate(doc, start=1):
            text = _extract_multicolumn_text(page)
            extraction = "text"
            if len(_compact_text(text)) < MIN_TEXT_CHARS_PER_PAGE:
                if ocr_ready:
                    ocr_text = _extract_ocr_text(page)
                    if len(_compact_text(ocr_text)) > len(_compact_text(text)):
                        text = ocr_text
                        extraction = "ocr"
                elif not _compact_text(text):
                    extraction = "empty"
            if not _compact_text(text) and extraction != "empty":
                extraction = "empty"
            pages.append(PageText(page=page_index, text=text.strip(), extraction=extraction))
    return pages


def is_ocr_available() -> bool:
    pytesseract = _load_pytesseract()
    if pytesseract is None:
        return False
    if not _tesseract_command():
        return False
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        return False
    return True


def chunk_pages(pages: list[PageText], source_name: str, document_id: str) -> list[TextChunk]:
    chunks: list[TextChunk] = []
    for page in pages:
        for index, text in enumerate(_split_text(page.text), start=1):
            chunk_id = f"{document_id}:p{page.page}:c{index}"
            chunks.append(
                TextChunk(
                    id=chunk_id,
                    text=text,
                    metadata={
                        "document_id": document_id,
                        "source": source_name,
                        "page": page.page,
                        "chunk": index,
                        "extraction": page.extraction,
                    },
                )
            )
    return chunks


def _extract_multicolumn_text(page: fitz.Page) -> str:
    raw = page.get_text("blocks", sort=False)
    blocks = []
    for block in raw:
        x0, y0, x1, y1, text, *_ = block
        text = _normalize_text(text)
        if text:
            blocks.append((float(x0), float(y0), float(x1), float(y1), text))

    if not blocks:
        return ""

    columns = _cluster_columns(blocks, page.rect.width)
    ordered_text: list[str] = []
    for column in columns:
        for _, _, _, _, text in sorted(column, key=lambda b: (b[1], b[0])):
            ordered_text.append(text)
    return "\n\n".join(ordered_text)


def _cluster_columns(
    blocks: list[tuple[float, float, float, float, str]], page_width: float
) -> list[list[tuple[float, float, float, float, str]]]:
    body_blocks = [b for b in blocks if b[2] - b[0] < page_width * 0.88]
    if len(body_blocks) < 4:
        return [sorted(blocks, key=lambda b: (b[1], b[0]))]

    centers = sorted((b[0] + b[2]) / 2 for b in body_blocks)
    gaps = [(centers[i + 1] - centers[i], i) for i in range(len(centers) - 1)]
    if not gaps:
        return [sorted(blocks, key=lambda b: (b[1], b[0]))]

    largest_gap, gap_index = max(gaps)
    if largest_gap < page_width * 0.18:
        return [sorted(blocks, key=lambda b: (b[1], b[0]))]

    split_x = (centers[gap_index] + centers[gap_index + 1]) / 2
    left: list[tuple[float, float, float, float, str]] = []
    right: list[tuple[float, float, float, float, str]] = []
    full_width: list[tuple[float, float, float, float, str]] = []

    for block in blocks:
        x0, _, x1, _, _ = block
        if x0 < page_width * 0.1 and x1 > page_width * 0.9:
            full_width.append(block)
        elif (x0 + x1) / 2 <= split_x:
            left.append(block)
        else:
            right.append(block)

    full_width.sort(key=lambda b: (b[1], b[0]))
    columns = []
    if full_width:
        columns.append(full_width)
    if left:
        columns.append(left)
    if right:
        columns.append(right)
    return columns


def _extract_ocr_text(page: fitz.Page) -> str:
    pytesseract = _load_pytesseract()
    if pytesseract is None:
        return ""

    zoom = OCR_DPI / 72
    matrix = fitz.Matrix(zoom, zoom)
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image = Image.open(io.BytesIO(pixmap.tobytes("png")))
    try:
        return _normalize_text(pytesseract.image_to_string(image, lang=OCR_LANGUAGE))
    except (pytesseract.TesseractNotFoundError, pytesseract.TesseractError):
        return ""


def _load_pytesseract():
    try:
        import pytesseract
    except ImportError:
        return None

    command = _tesseract_command()
    if command:
        pytesseract.pytesseract.tesseract_cmd = command
    return pytesseract


def _tesseract_command() -> str | None:
    if TESSERACT_CMD:
        return TESSERACT_CMD
    return shutil.which("tesseract")


def _split_text(text: str) -> list[str]:
    text = _normalize_text(text)
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(current) + len(paragraph) + 2 <= CHUNK_SIZE:
            current = f"{current}\n\n{paragraph}".strip()
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= CHUNK_SIZE:
            current = paragraph
        else:
            chunks.extend(_split_long_paragraph(paragraph))
            current = ""

    if current:
        chunks.append(current)

    if CHUNK_OVERLAP <= 0 or len(chunks) <= 1:
        return chunks

    overlapped: list[str] = []
    previous_tail = ""
    for chunk in chunks:
        combined = f"{previous_tail}\n{chunk}".strip() if previous_tail else chunk
        overlapped.append(combined)
        previous_tail = chunk[-CHUNK_OVERLAP:]
    return overlapped


def _split_long_paragraph(paragraph: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    while start < len(paragraph):
        end = min(start + CHUNK_SIZE, len(paragraph))
        pieces.append(paragraph[start:end].strip())
        start = max(end - CHUNK_OVERLAP, end)
    return [piece for piece in pieces if piece]


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text)
