from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from langchain_openai import ChatOpenAI
from langchain_qdrant import QdrantVectorStore

from src.schemas import QueryPlan, StartupProfile
from src.utils.references import dedupe_keep_order, format_rag_reference
from src.utils.text import model_to_pretty_json, shorten


@dataclass(slots=True)
class RetrievedChunk:
    content: str
    metadata: dict

    def key(self) -> tuple[str, int, str]:
        return (
            str(self.metadata.get("doc_id", "")),
            int(self.metadata.get("page", 0)),
            shorten(self.content, 120),
        )

    def to_context_block(self, limit: int = 2000) -> str:
        return (
            f"[doc_id] {self.metadata.get('doc_id', '')}\n"
            f"[title] {self.metadata.get('title', '')}\n"
            f"[issuer] {self.metadata.get('issuer', '')}\n"
            f"[year] {self.metadata.get('year', '')}\n"
            f"[page] {self.metadata.get('page', '')}\n"
            f"[content] {shorten(self.content, limit)}\n"
        )

    def to_reference(self) -> str:
        return format_rag_reference(
            issuer=self.metadata.get("issuer", "Unknown"),
            year=self.metadata.get("year") or None,
            title=self.metadata.get("title", "Untitled"),
            source_url=self.metadata.get("source_url") or None,
            filename=self.metadata.get("filename") or None,
            page=self.metadata.get("page"),
        )


class AgenticRAGRetriever:
    def __init__(self, llm: ChatOpenAI, vector_store: QdrantVectorStore) -> None:
        self.llm = llm
        self.vector_store = vector_store

    def plan_queries(
        self,
        *,
        task_name: str,
        startup_profile: StartupProfile,
        extra_focus: str,
    ) -> list[str]:
        structured_llm = self.llm.with_structured_output(QueryPlan, method="json_schema")
        response = structured_llm.invoke(
            [
                (
                    "system",
                    "You create focused retrieval queries for a local RAG corpus."
                    " Return 3 to 4 concise queries.",
                ),
                (
                    "human",
                    f"Task: {task_name}\n"
                    f"Focus: {extra_focus}\n"
                    f"Startup profile:\n{model_to_pretty_json(startup_profile)}",
                ),
            ]
        )
        queries = [q.strip() for q in response.queries if q and q.strip()]
        if not queries:
            queries = [
                f"{startup_profile.name} manufacturing AI deployment",
                f"{startup_profile.core_product} manufacturing adoption",
                "manufacturing AI deployment barriers",
            ]
        return queries[:4]

    def retrieve(
        self,
        queries: Iterable[str],
        *,
        tags: list[str],
        per_query_k: int = 6,
        max_total: int = 8,
    ) -> list[RetrievedChunk]:
        collected: list[RetrievedChunk] = []
        seen: set[tuple[str, int, str]] = set()

        for query in queries:
            docs = self.vector_store.similarity_search(query, k=max(per_query_k * 2, per_query_k))
            for doc in docs:
                metadata = dict(doc.metadata)
                tags_text = str(metadata.get("tags_text", ""))
                tag_set = {tag.strip() for tag in tags_text.split(",") if tag.strip()}
                if tags and not tag_set.intersection(tags):
                    continue

                chunk = RetrievedChunk(content=doc.page_content, metadata=metadata)
                key = chunk.key()
                if key in seen:
                    continue
                seen.add(key)
                collected.append(chunk)
                if len(collected) >= max_total:
                    return collected
        return collected

    @staticmethod
    def to_context(chunks: list[RetrievedChunk], limit: int = 1800) -> str:
        if not chunks:
            return "No local RAG evidence found."
        return "\n---\n".join(chunk.to_context_block(limit=limit) for chunk in chunks)

    @staticmethod
    def to_references(chunks: list[RetrievedChunk]) -> list[str]:
        return dedupe_keep_order(chunk.to_reference() for chunk in chunks)
