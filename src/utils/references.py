from __future__ import annotations

from typing import Iterable

from src.utils.text import domain_from_url


def dedupe_keep_order(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        normalized = item.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        output.append(normalized)
    return output


def format_web_reference(title: str, url: str, published_date: str | None = None) -> str:
    issuer = domain_from_url(url)
    date_text = published_date or "n.d."
    return f"{issuer} ({date_text}). *{title}*. {url}"


def format_rag_reference(
    issuer: str,
    year: str | None,
    title: str,
    source_url: str | None = None,
    filename: str | None = None,
    page: int | None = None,
) -> str:
    year_text = year or "n.d."
    location = source_url or filename or ""
    page_text = f" (p.{page})" if page else ""
    return f"{issuer} ({year_text}). *{title}*{page_text}. {location}".strip()
