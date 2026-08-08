"""Tests for document ingestion: PDF/DOCX → chunks with metadata.

Uses real fixture text encoded as bytes (no actual PDF binary needed for unit tests).
"""
import pytest
from unittest.mock import patch, MagicMock


def test_split_text_basic():
    """Text splitter must return non-empty chunks."""
    from ingestion import _split_text
    text = "This is a long document. " * 100
    chunks = _split_text(text, chunk_size=300, overlap=50)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) > 0
        assert len(chunk) <= 300 + 50  # allow some overlap tolerance


def test_split_text_empty():
    """Empty text must return empty list."""
    from ingestion import _split_text
    assert _split_text("", chunk_size=300, overlap=50) == []
    assert _split_text("   ", chunk_size=300, overlap=50) == []


def test_split_text_short():
    """Text shorter than chunk_size should return a single chunk."""
    from ingestion import _split_text
    text = "Short text."
    chunks = _split_text(text, chunk_size=300, overlap=50)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_ingest_unsupported_type_raises():
    """Unsupported file types must raise ValueError."""
    from ingestion import ingest_file
    with pytest.raises(ValueError, match="Unsupported file type"):
        ingest_file(b"data", "document.txt", "doc_001")


def test_ingest_pdf_returns_chunks():
    """PDF ingestion must return Document + non-empty chunks."""
    from ingestion import ingest_pdf
    # Create minimal valid PDF bytes using reportlab mock
    mock_page = MagicMock()
    mock_page.extract_text.return_value = (
        "This is a test privacy policy. We collect your data for service improvement. "
        "We retain data for 30 days. You may withdraw consent at any time. " * 20
    )
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("ingestion.PdfReader", return_value=mock_reader):
        doc, chunks = ingest_pdf(b"fake_pdf_bytes", "doc_001", "test.pdf")

    assert doc.filename == "test.pdf"
    assert doc.file_type == "pdf"
    assert len(chunks) > 0
    assert doc.total_chunks == len(chunks)

    for chunk in chunks:
        assert chunk.doc_id == "doc_001"
        assert chunk.text
        assert chunk.page_number == 1  # all from page 1 in our mock


def test_ingest_docx_returns_chunks():
    """DOCX ingestion must return Document + non-empty chunks with section metadata."""
    from ingestion import ingest_docx

    mock_para_heading = MagicMock()
    mock_para_heading.style.name = "Heading 1"
    mock_para_heading.text = "Data Retention Policy"

    mock_para_body = MagicMock()
    mock_para_body.style.name = "Normal"
    mock_para_body.text = (
        "We retain your personal data for 30 days after account closure. "
        "This is in compliance with DPDP 2023. " * 15
    )

    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para_heading, mock_para_body]

    with patch("ingestion.DocxDocument", return_value=mock_doc):
        doc, chunks = ingest_docx(b"fake_docx_bytes", "doc_002", "test.docx")

    assert doc.file_type == "docx"
    assert len(chunks) > 0
    # Section title should be set from the heading
    assert any(c.section_title == "Data Retention Policy" for c in chunks)


def test_chunk_ids_are_unique():
    """All chunk IDs in a document must be unique."""
    from ingestion import ingest_pdf

    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Content. " * 200
    mock_reader = MagicMock()
    mock_reader.pages = [mock_page, mock_page]  # 2 pages

    with patch("ingestion.PdfReader", return_value=mock_reader):
        _, chunks = ingest_pdf(b"fake", "doc_001", "test.pdf")

    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "Chunk IDs must be unique"
