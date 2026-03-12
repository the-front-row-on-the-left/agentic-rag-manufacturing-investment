from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field
from pypdf import PdfReader

from src.config import Settings
from src.utils.io import ensure_dir
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


class CorpusManifest(BaseModel):
    documents: list[ManifestItem] = Field(default_factory=list)


class VectorStoreManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
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

    def build_or_load(self, rebuild: bool = False) -> Chroma:
        ensure_dir(self.settings.chroma_dir)

        if rebuild and self.settings.chroma_dir.exists():
            shutil.rmtree(self.settings.chroma_dir, ignore_errors=True)
            ensure_dir(self.settings.chroma_dir)

        vector_store = Chroma(
            collection_name=self.settings.chroma_collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.settings.chroma_dir),
        )

        if rebuild or self._is_empty(vector_store):
            chunks = self._load_and_split_documents()
            if chunks:
                ids = [f"{doc.metadata['doc_id']}-p{doc.metadata['page']}-c{i}" for i, doc in enumerate(chunks)]
                vector_store.add_documents(chunks, ids=ids)
        return vector_store

    def _is_empty(self, vector_store: Chroma) -> bool:
        try:
            return vector_store._collection.count() == 0
        except Exception:
            return True

    def _load_and_split_documents(self) -> list[Document]:
        manifest = self.load_manifest()
        raw_pages: list[Document] = []

        for item in manifest.documents:
            path = self.settings.rag_docs_dir / item.filename
            if not path.exists():
                continue

            reader = PdfReader(str(path))
            for page_no, page in enumerate(reader.pages, start=1):
                text = clean_whitespace(page.extract_text() or "")
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
                            "tags_text": ",".join(item.tags),
                            "page": page_no,
                        },
                    )
                )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )
        return splitter.split_documents(raw_pages)
