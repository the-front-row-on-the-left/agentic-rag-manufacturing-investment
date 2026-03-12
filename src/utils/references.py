from __future__ import annotations

import re
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


def merge_rag_references(references: list[str]) -> list[str]:
    """동일 문서의 페이지별 RAG 레퍼런스를 하나로 병합한다.

    예시 입력:
        OECD (2021). *AI in Manufacturing* (p.4). docs1.pdf
        OECD (2021). *AI in Manufacturing* (p.6). docs1.pdf
        OECD (2021). *AI in Manufacturing* (p.8). docs1.pdf
    예시 출력:
        OECD (2021). *AI in Manufacturing* (pp.4, 6, 8). docs1.pdf
    """
    page_pattern = re.compile(r"^(.*?)\s*\(p\.(\d+)\)\.?\s*(.*)$")

    # key: (prefix, suffix) → pages
    grouped: dict[tuple[str, str], list[int]] = {}
    order: list[tuple[str, str]] = []  # 삽입 순서 유지
    non_rag: list[str] = []

    for ref in references:
        ref = ref.strip()
        m = page_pattern.match(ref)
        if m:
            prefix = m.group(1).strip()
            page = int(m.group(2))
            suffix = m.group(3).strip()
            key = (prefix, suffix)
            if key not in grouped:
                grouped[key] = []
                order.append(key)
            grouped[key].append(page)
        else:
            non_rag.append(ref)

    merged: list[str] = []
    for key in order:
        prefix, suffix = key
        pages = sorted(set(grouped[key]))
        if len(pages) == 1:
            page_text = f"(p.{pages[0]})"
        else:
            page_text = "(pp." + ", ".join(str(p) for p in pages) + ")"
        location = f". {suffix}" if suffix else ""
        merged.append(f"{prefix} {page_text}{location}".strip())

    return merged + non_rag