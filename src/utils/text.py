from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel


def clean_whitespace(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def model_to_pretty_json(model: BaseModel | dict[str, Any]) -> str:
    if isinstance(model, BaseModel):
        payload = model.model_dump()
    else:
        payload = model
    return json.dumps(payload, ensure_ascii=False, indent=2)


def shorten(text: str, limit: int = 5000) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def domain_from_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        return hostname.replace("www.", "")
    except Exception:
        return "unknown-source"
