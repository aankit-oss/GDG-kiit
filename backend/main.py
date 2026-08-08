"""FastAPI application entry point for LexAudit."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routers import audit, documents, qa

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: ensure required directories exist."""
    Path(settings.chroma_persist_path).mkdir(parents=True, exist_ok=True)
    Path(settings.reports_dir).mkdir(parents=True, exist_ok=True)
    (Path(settings.reports_dir) / "audit").mkdir(parents=True, exist_ok=True)
    logger.info("LexAudit backend starting up")
    logger.info("ChromaDB path: %s", settings.chroma_persist_path)
    logger.info("Reports path: %s", settings.reports_dir)
    logger.info("NVIDIA model: %s", settings.nvidia_model)
    yield
    logger.info("LexAudit backend shutting down")


app = FastAPI(
    title="LexAudit API",
    description=(
        "Compliance-audit and grounded Q&A agent for Indian law documents. "
        "Covers DPDP 2023 and Indian Contract Act 1872."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(documents.router)
app.include_router(audit.router)
app.include_router(qa.router)


@app.get("/")
async def root() -> dict:
    return {
        "name": "LexAudit API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health() -> dict:
    """Health check endpoint for Docker/CI."""
    from vector_store import get_vector_store
    vs = get_vector_store()
    return {
        "status": "ok",
        "chunk_count": vs.chunk_count(),
    }
