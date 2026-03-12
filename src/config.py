from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


@dataclass(slots=True)
class Settings:
    base_dir: Path
    data_dir: Path
    rag_docs_dir: Path
    output_dir: Path
    openai_api_key: str
    openai_model: str
    tavily_api_key: str
    domain: str
    input_keyword: str
    max_candidates: int
    embedding_model_name: str
    chunk_size: int
    chunk_overlap: int
    top_k_tech: int
    top_k_market: int
    qdrant_url: str
    qdrant_api_key: str | None
    qdrant_collection_name: str


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Environment variable '{name}' is required.")
    return value


@lru_cache(maxsize=1)
def get_settings(
    input_keyword: str | None = None,
    domain: str | None = None,
    max_candidates: int | None = None,
) -> Settings:
    base_dir = BASE_DIR
    data_dir = base_dir / "data"
    rag_docs_dir = data_dir / "rag_docs"
    output_dir = base_dir / "outputs"

    return Settings(
        base_dir=base_dir,
        data_dir=data_dir,
        rag_docs_dir=rag_docs_dir,
        output_dir=output_dir,
        openai_api_key=_require_env("OPENAI_API_KEY"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(),
        tavily_api_key=_require_env("TAVILY_API_KEY"),
        domain=(domain or os.getenv("DOMAIN", "manufacturing")).strip(),
        input_keyword=(input_keyword or os.getenv("INPUT_KEYWORD", "manufacturing AI startup")).strip(),
        max_candidates=int(max_candidates or os.getenv("MAX_CANDIDATES", "5")),
        embedding_model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-m3").strip(),
        chunk_size=int(os.getenv("CHUNK_SIZE", "1200")),
        chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
        top_k_tech=int(os.getenv("TOP_K_TECH", "6")),
        top_k_market=int(os.getenv("TOP_K_MARKET", "6")),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333").strip(),
        qdrant_api_key=os.getenv("QDRANT_API_KEY", "").strip() or None,
        qdrant_collection_name=os.getenv(
            "QDRANT_COLLECTION_NAME", "manufacturing_startup_eval"
        ).strip(),
    )
