"""Application configuration via environment variables."""
from pathlib import Path

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM API Keys
    nvidia_api_key: str = ""
    gemini_api_key: str = ""

    # NVIDIA NIM endpoint (OpenAI-compatible)
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "meta/llama-3.1-70b-instruct"

    # ChromaDB persistence
    chroma_persist_path: str = "./chroma_data"
    chroma_collection_name: str = "lexaudit_chunks"

    # Rules directory
    rules_dir: str = str(Path(__file__).parent.parent / "rules")

    # Audit reports persistence
    reports_dir: str = "./audit_reports"

    # Grounding threshold (0.0 - 1.0)
    grounding_threshold: float = 0.65
    grounding_max_chunks: int = 5

    # Chunking config
    chunk_size: int = 800       # characters
    chunk_overlap: int = 150    # characters

    # App
    app_name: str = "LexAudit"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]


settings = Settings()
