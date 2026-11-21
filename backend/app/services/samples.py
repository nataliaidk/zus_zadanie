from __future__ import annotations

import json
from pathlib import Path

from app.models.schemas import ParentProfile
from app.services.pdf_fixtures_map import pdf_for_kind
from app.services.pdf_parser import parse_and_calculate
from app.services.rule_engine import calculate

DATA = Path(__file__).resolve().parent.parent / "data" / "samples.json"


def list_samples() -> list[dict]:
    return json.loads(DATA.read_text(encoding="utf-8"))


def sample_pdf(sample_id: str) -> tuple[dict, bytes]:
    for item in list_samples():
        if item["id"] == sample_id:
            return item, pdf_for_kind(item["kind"], item.get("benefit_base_pln"))
    raise KeyError(sample_id)


def calculate_sample(sample_id: str, params: dict) -> dict:
    meta, pdf = sample_pdf(sample_id)
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
