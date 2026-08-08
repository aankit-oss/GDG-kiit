"""Documents router — upload and ingest PDF/DOCX files."""
from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from config import settings
from ingestion import ingest_file
from models import Document, UploadResponse
from vector_store import get_vector_store

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Persist document metadata to disk (simple JSON store)
_DOCS_STORE_PATH = Path(settings.reports_dir) / "documents.json"


def _load_docs() -> dict[str, dict]:
    if _DOCS_STORE_PATH.exists():
        with open(_DOCS_STORE_PATH, "r") as f:
            return json.load(f)
    return {}


def _save_docs(docs: dict[str, dict]) -> None:
    _DOCS_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_DOCS_STORE_PATH, "w") as f:
        json.dump(docs, f, indent=2, default=str)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a PDF or DOCX document, parse it into chunks, and store in vector DB.

    Returns doc_id for use in subsequent audit and Q&A requests.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".docx", ".doc"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Only PDF and DOCX are supported.",
        )

    file_bytes = await file.read()
    if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB.")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Empty file uploaded.")

    try:
        # Use filename as seed for doc_id prefix for deterministic naming
        from uuid import uuid4
        doc_id = f"doc_{uuid4().hex[:12]}"
        doc, chunks = ingest_file(file_bytes, file.filename, doc_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Ingestion failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No text could be extracted from the uploaded file.",
        )

    # Store in vector DB
    try:
        vs = get_vector_store()
        vs.add_chunks(chunks)
    except Exception as e:
        logger.exception("Vector store indexing failed for %s", file.filename)
        raise HTTPException(
            status_code=500,
            detail=f"Vector indexing failed: {e}. Check network connection for model download.",
        )

    # Persist document metadata
    docs = _load_docs()
    docs[doc.doc_id] = doc.model_dump(mode="json")
    _save_docs(docs)

    logger.info("Uploaded %s → %s (%d chunks)", file.filename, doc_id, len(chunks))

    return UploadResponse(
        doc_id=doc.doc_id,
        filename=doc.filename,
        total_chunks=doc.total_chunks,
        message=f"Document ingested successfully into {doc.total_chunks} chunks.",
    )


@router.get("/{doc_id}")
async def get_document(doc_id: str) -> dict:
    """Get document metadata by doc_id."""
    docs = _load_docs()
    if doc_id not in docs:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return docs[doc_id]


@router.get("/")
async def list_documents() -> list[dict]:
    """List all uploaded documents."""
    return list(_load_docs().values())
