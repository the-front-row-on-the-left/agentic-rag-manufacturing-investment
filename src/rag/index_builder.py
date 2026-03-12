from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

import fitz
from langchain_core.documents import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field, model_validator
from qdrant_client import QdrantClient, models

from src.config import Settings
from src.utils.text import clean_whitespace


class ManifestItem(BaseModel):
    doc_id: str
    filename: str
    title: str
    issuer: str
    year: str | None = None
    source_type: str = "report"
    tags: list[str] = Field(default_factory=list)
    source_url: str | None = None
    authors: str | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        normalized = dict(data)
        filename = normalized.get("filename") or normalized.get("file")
        title = normalized.get("title") or normalized.get("doc_id") or filename or "untitled"

        normalized["filename"] = filename
        normalized["title"] = title
        normalized["doc_id"] = normalized.get("doc_id") or Path(str(filename or title)).stem
        normalized["issuer"] = normalized.get("issuer") or normalized.get("organization") or "unknown"
        normalized["year"] = (
            None if normalized.get("year") in (None, "") else str(normalized.get("year"))
        )
        normalized["source_type"] = normalized.get("source_type") or normalized.get("domain") or "report"
        normalized["tags"] = normalized.get("tags") or []
        normalized["source_url"] = normalized.get("source_url")
        normalized["authors"] = normalized.get("authors")
        return normalized


class CorpusManifest(BaseModel):
    documents: list[ManifestItem] = Field(default_factory=list)


class VectorStoreManager:
    MIN_CHUNK_CHARS = 120
    MIN_CHUNK_WORDS = 20

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.embedding_model_name,
            encode_kwargs={"normalize_embeddings": True},
        )

    @property
    def manifest_path(self) -> Path:
        return self.settings.rag_docs_dir / "manifest.json"

    def load_manifest(self) -> CorpusManifest:
        if not self.manifest_path.exists():
            return CorpusManifest()
        payload = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return CorpusManifest.model_validate(payload)

    def build_index(self, rebuild: bool = False) -> QdrantVectorStore:
        self._ensure_collection(rebuild=rebuild)
        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=self.settings.qdrant_collection_name,
            embedding=self.embeddings,
        )

        chunks = self._load_and_split_documents()
        if chunks:
            ids = [
                str(
                    uuid.uuid5(
                        uuid.NAMESPACE_URL,
                        f"{doc.metadata['doc_id']}-p{doc.metadata['page']}-c{i}",
                    )
                )
                for i, doc in enumerate(chunks)
            ]
            vector_store.add_documents(chunks, ids=ids)
        return vector_store

    def load_existing(self) -> QdrantVectorStore:
        collection_name = self.settings.qdrant_collection_name
        existing = {
            collection.name for collection in self.client.get_collections().collections
        }
        if collection_name not in existing:
            raise RuntimeError(
                "Vector index does not exist. Run `uv run python build_index.py` first."
            )

        vector_store = QdrantVectorStore(
            client=self.client,
            collection_name=collection_name,
            embedding=self.embeddings,
        )
        if self._is_empty(vector_store):
            raise RuntimeError(
                "Vector index is empty. Run `uv run python build_index.py` first."
            )
        return vector_store

    def _is_empty(self, vector_store: QdrantVectorStore) -> bool:
        try:
            count = self.client.count(
                collection_name=self.settings.qdrant_collection_name,
                exact=True,
            )
            return count.count == 0
        except Exception:
            return True

    def _ensure_collection(self, rebuild: bool) -> None:
        collection_name = self.settings.qdrant_collection_name
        existing = {
            collection.name for collection in self.client.get_collections().collections
        }

        if rebuild and collection_name in existing:
            self.client.delete_collection(collection_name=collection_name)
            existing.remove(collection_name)

        if collection_name in existing:
            return

        embedding_size = len(self.embeddings.embed_query("manufacturing ai"))
        self.client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=embedding_size,
                distance=models.Distance.COSINE,
            ),
        )

    def _load_and_split_documents(self) -> list[Document]:
        manifest = self.load_manifest()
        raw_pages: list[Document] = []

        for item in manifest.documents:
            path = self.settings.rag_docs_dir / item.filename
            if not path.exists():
                continue

            with fitz.open(path) as pdf:
                for page_no, page in enumerate(pdf, start=1):
                    text = self._extract_page_text(page, item=item, page_no=page_no)
                    if not text:
                        continue
                    raw_pages.append(
                        Document(
                            page_content=text,
                            metadata={
                                "doc_id": item.doc_id,
                                "filename": item.filename,
                                "title": item.title,
                                "issuer": item.issuer,
                                "year": item.year or "",
                                "source_type": item.source_type,
                                "source_url": item.source_url or "",
                                "authors": item.authors or "",
                                "tags_text": self._build_tags_text(item),
                                "page": page_no,
                            },
                        )
                    )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        chunks = splitter.split_documents(raw_pages)
        return [chunk for chunk in chunks if self._is_meaningful_chunk(chunk.page_content)]

    def _extract_page_text(self, page: Any, item: ManifestItem, page_no: int) -> str:
        text = self._extract_page_text_standard(page)
        lines = [line.strip() for line in text.splitlines()]
        cleaned_lines: list[str] = []
        previous_blank = False

        for line in lines:
            line = clean_whitespace(line)
            if not line:
                previous_blank = True
                continue
            if self._should_drop_line(line=line, item=item, page_no=page_no):
                continue
            if previous_blank and cleaned_lines:
                cleaned_lines.append("")
            cleaned_lines.append(line)
            previous_blank = False

        cleaned_text = "\n".join(cleaned_lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
        return clean_whitespace(cleaned_text)

    def _extract_page_text_standard(self, page: Any) -> str:
        return page.get_text("text", sort=True) or ""

    def _build_tags_text(self, item: ManifestItem) -> str:
        tags = {tag.strip() for tag in item.tags if tag and tag.strip()}
        tags.add("manufacturing")

        if item.doc_id in {"docs1", "docs2"}:
            tags.add("tech")
        if item.doc_id in {"docs3", "docs4"}:
            tags.add("market")

        return ",".join(sorted(tags))

    def _should_drop_line(self, line: str, item: ManifestItem, page_no: int) -> bool:
        normalized = line.strip()
        normalized_lower = normalized.lower()
        title_lower = item.title.lower()

        if normalized.isdigit():
            return True
        if re.fullmatch(r"\d+\s*\|", normalized):
            return True
        if re.fullmatch(r"\|\s*\d+", normalized):
            return True
        if normalized in {"|", "•"}:
            return True
        if re.fullmatch(r"chart\s+\d+", normalized_lower):
            return True
        if normalized_lower == title_lower:
            return True
        if title_lower in normalized_lower and str(page_no) in normalized:
            return True
        if item.issuer and item.issuer.lower() in normalized_lower and str(page_no) in normalized:
            return True
        if len(normalized) <= 40 and normalized == normalized.upper() and re.search(r"[A-Z]", normalized):
            return True
        if item.doc_id == "docs3" and self._is_docs3_chart_noise(normalized):
            return True
        return False

    def _is_docs3_chart_noise(self, line: str) -> bool:
        lower = line.lower()
        if lower.startswith(("figure ", "chart ", "table ")):
            return True
        if "source:" in lower:
            return True

        words = line.split()
        if len(words) >= 8 and sum(1 for word in words if len(word) <= 3) / len(words) > 0.7:
            return True

        alpha_chars = sum(1 for char in line if char.isalpha())
        digit_chars = sum(1 for char in line if char.isdigit())
        symbol_chars = sum(1 for char in line if not char.isalnum() and not char.isspace())
        total_visible = alpha_chars + digit_chars + symbol_chars

        if total_visible and (digit_chars + symbol_chars) / total_visible > 0.45:
            return True

        if len(words) <= 8 and alpha_chars and line == line.title() and digit_chars == 0:
            return True

        return False

    def _is_meaningful_chunk(self, content: str) -> bool:
        normalized = clean_whitespace(content)
        if len(normalized) < self.MIN_CHUNK_CHARS:
            return False

        words = normalized.split()
        if len(words) < self.MIN_CHUNK_WORDS:
            return False

        alpha_chars = sum(1 for char in normalized if char.isalpha())
        if alpha_chars < 40:
            return False

        return True
