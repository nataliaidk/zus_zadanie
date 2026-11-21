from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import ParentProfile
from app.services.pdf_fixtures_map import pdf_for_kind
from app.services.pdf_parser import parse_and_calculate
from app.services.rule_engine import calculate

DATA = Path(__file__).resolve().parent.parent / "data" / "samples.json"
SPRAWY = Path(__file__).resolve().parent.parent / "data" / "sprawy"
INDEX = SPRAWY / "index.json"

_PUBLIC = ("id", "title", "document", "outcome", "kind", "filename", "benefit_base_pln")


def _sprawy() -> list[dict]:
    if not INDEX.exists():
        return []
    items = json.loads(INDEX.read_text(encoding="utf-8"))
    public: list[dict] = []
    for item in items:
        row = {key: item[key] for key in _PUBLIC if key in item}
        row.setdefault("kind", "sprawa")
        overlay = item.get("overlay") or {}
        row.setdefault("benefit_base_pln", overlay.get("benefit_base_pln"))
        public.append(row)
    return public


def _catalog() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def list_samples() -> list[dict]:
    return _sprawy() + _catalog()


def _sprawa_raw(sample_id: str) -> dict | None:
    if not INDEX.exists():
        return None
    for item in json.loads(INDEX.read_text(encoding="utf-8")):
        if item["id"] == sample_id:
            return item
    return None


def sample_pdf(sample_id: str) -> tuple[dict, bytes]:
    sprawa = _sprawa_raw(sample_id)
    if sprawa:
        pdf_path = SPRAWY / sprawa["filename"]
        return sprawa, pdf_path.read_bytes()
    for item in _catalog():
        if item["id"] == sample_id:
            return item, pdf_for_kind(item["kind"], item.get("benefit_base_pln"))
    raise KeyError(sample_id)


def calculate_sample(sample_id: str, params: dict) -> dict:
    meta, pdf = sample_pdf(sample_id)
    if meta.get("kind") == "sprawa" or meta.get("filename"):
        result = parse_and_calculate(pdf, params, source_name=meta.get("filename"))
        payload = result.model_dump(mode="json")
        payload["sample"] = {key: meta[key] for key in _PUBLIC if key in meta}
        if meta.get("outcome"):
            payload["plain_language"] = meta["outcome"]
        return payload
    if meta.get("profile"):
        profile = ParentProfile.model_validate(meta["profile"])
        result = calculate(profile, params)
        return {
            "sample": meta,
            "document_type": "sample",
            "document_code": meta.get("document"),
            "profile": profile.model_dump(mode="json"),
            "calculation": result.model_dump(mode="json"),
            "plain_language": meta.get("outcome"),
            "missing_fields": [],
        }
    result = parse_and_calculate(pdf, params)
    payload = result.model_dump(mode="json")
    payload["sample"] = meta
    return payload
