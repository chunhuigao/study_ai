from pathlib import Path

import fitz

from app.pdf_pipeline import chunk_pages, document_id_for, extract_pdf_pages


def test_extracts_multicolumn_pdf_in_column_order(tmp_path: Path) -> None:
    path = tmp_path / "columns.pdf"
    doc = fitz.open()
    page = doc.new_page(width=600, height=800)
    page.insert_textbox(fitz.Rect(60, 80, 260, 260), "left one\nleft two", fontsize=12)
    page.insert_textbox(fitz.Rect(330, 80, 540, 260), "right one\nright two", fontsize=12)
    doc.save(path)
    doc.close()

    pages = extract_pdf_pages(path)

    assert len(pages) == 1
    assert "left one" in pages[0].text
    assert pages[0].text.index("left one") < pages[0].text.index("right one")


def test_chunks_include_source_metadata(tmp_path: Path) -> None:
    path = tmp_path / "simple.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "A concise PDF paragraph about retrieval augmented generation.")
    doc.save(path)
    doc.close()

    document_id = document_id_for(path)
    pages = extract_pdf_pages(path)
    chunks = chunk_pages(pages, "simple.pdf", document_id)

    assert chunks
    assert chunks[0].metadata["source"] == "simple.pdf"
    assert chunks[0].metadata["page"] == 1
    assert chunks[0].metadata["document_id"] == document_id


def test_marks_empty_page_when_ocr_is_unavailable(tmp_path: Path, monkeypatch) -> None:
    path = tmp_path / "empty.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(path)
    doc.close()
    monkeypatch.setattr("app.pdf_pipeline.is_ocr_available", lambda: False)

    pages = extract_pdf_pages(path)
    chunks = chunk_pages(pages, "empty.pdf", document_id_for(path))

    assert pages[0].extraction == "empty"
    assert chunks == []
