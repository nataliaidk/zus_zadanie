"""Optional LLM for PDF field phrasing and chat wording. Never used for amounts."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import httpx

TIMEOUT_SECONDS = 12


def llm_configured() -> bool:
    return bool(os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"))


def complete(prompt: str, *, system: str | None = None) -> Optional[str]:
    api_key = os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    base = os.environ.get("LLM_API_BASE", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    try:
        response = httpx.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": messages, "temperature": 0},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, IndexError, TypeError):
        return None


def complete_json(prompt: str, *, system: str | None = None) -> Optional[dict[str, Any]]:
    raw = complete(prompt, system=system)
    if not raw:
        return None
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None
