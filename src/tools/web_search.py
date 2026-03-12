from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tavily import TavilyClient
from tavily.errors import BadRequestError

from src.utils.references import dedupe_keep_order, format_web_reference
from src.utils.text import clean_whitespace, shorten

MAX_TAVILY_QUERY_LENGTH = 400


@dataclass(slots=True)
class SearchResult:
    query: str
    title: str
    url: str
    content: str
    raw_content: str | None = None
    score: float | None = None
    published_date: str | None = None

    def to_context_block(self, raw_limit: int = 4000) -> str:
        raw = shorten(clean_whitespace(self.raw_content or ""), raw_limit)
        summary = shorten(clean_whitespace(self.content or ""), 1200)
        return (
            f"[query] {self.query}\n"
            f"[title] {self.title}\n"
            f"[url] {self.url}\n"
            f"[published_date] {self.published_date or 'n/a'}\n"
            f"[summary] {summary}\n"
            f"[raw_content] {raw}\n"
        )

    def to_reference(self) -> str:
        return format_web_reference(
            title=self.title,
            url=self.url,
            published_date=self.published_date,
        )


class TavilySearchTool:
    def __init__(self, api_key: str) -> None:
        self.client = TavilyClient(api_key=api_key)

    @staticmethod
    def _normalize_query(query: str, limit: int = MAX_TAVILY_QUERY_LENGTH) -> str:
        # Tavily rejects long queries; normalize and cap length before request.
        normalized = clean_whitespace(query or "")
        if not normalized:
            return ""
        if len(normalized) <= limit:
            return normalized
        return normalized[:limit].rstrip()

    def search(
        self,
        query: str,
        *,
        topic: str = "general",
        max_results: int = 5,
        exact_match: bool = False,
        include_domains: list[str] | None = None,
        time_range: str | None = None,
    ) -> list[SearchResult]:
        normalized_query = self._normalize_query(query)
        if not normalized_query:
            return []

        try:
            response = self.client.search(
                query=normalized_query,
                search_depth="advanced",
                topic=topic,
                max_results=max_results,
                include_raw_content="text",
                chunks_per_source=3,
                exact_match=exact_match,
                include_domains=include_domains or [],
                time_range=time_range,
            )
        except BadRequestError as exc:
            # Safety retry if provider-side length validation differs from local check.
            if "query is too long" not in str(exc).lower():
                raise
            fallback_query = self._normalize_query(normalized_query, limit=300)
            if not fallback_query:
                return []
            response = self.client.search(
                query=fallback_query,
                search_depth="advanced",
                topic=topic,
                max_results=max_results,
                include_raw_content="text",
                chunks_per_source=3,
                exact_match=exact_match,
                include_domains=include_domains or [],
                time_range=time_range,
            )
        results: list[SearchResult] = []
        for item in response.get("results", []):
            results.append(
                SearchResult(
                    query=normalized_query,
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    content=item.get("content", ""),
                    raw_content=item.get("raw_content"),
                    score=item.get("score"),
                    published_date=item.get("published_date"),
                )
            )
        return results

    def batch_search(
        self,
        queries: Iterable[str],
        *,
        topic: str = "general",
        max_results: int = 5,
        exact_match: bool = False,
        include_domains: list[str] | None = None,
        time_range: str | None = None,
        max_unique_results: int = 10,
    ) -> list[SearchResult]:
        seen_urls: set[str] = set()
        merged: list[SearchResult] = []

        for query in queries:
            normalized_query = self._normalize_query(query)
            if not normalized_query:
                continue
            for result in self.search(
                normalized_query,
                topic=topic,
                max_results=max_results,
                exact_match=exact_match,
                include_domains=include_domains,
                time_range=time_range,
            ):
                if not result.url or result.url in seen_urls:
                    continue
                seen_urls.add(result.url)
                merged.append(result)
                if len(merged) >= max_unique_results:
                    return merged
        return merged

    @staticmethod
    def to_context(results: list[SearchResult], raw_limit: int = 3500) -> str:
        if not results:
            return "No web search results."
        blocks = [result.to_context_block(raw_limit=raw_limit) for result in results]
        return "\n---\n".join(blocks)

    @staticmethod
    def to_references(results: list[SearchResult]) -> list[str]:
        refs = [result.to_reference() for result in results if result.url]
        return dedupe_keep_order(refs)
