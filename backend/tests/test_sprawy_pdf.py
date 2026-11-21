from pathlib import Path

from app.services.pdf_parser import parse_and_calculate
from app.services.samples import calculate_sample, list_samples, sample_pdf

SPRAWY = Path(__file__).resolve().parents[1] / "app" / "data" / "sprawy"

EXPECTED = {
    "sprawa-wa-05": {"combine": 82.0},
    "sprawa-war-02": {"family": "foster"},
    "sprawa-ta-2": {"sick": "chorobowy_ciaza", "mat": 20},
    "sprawa-ko-4": {"sick": "chorobowy_ciaza"},
    "sprawa-lu-2": {"supp": True, "mat": 20},
    "sprawa-no-3": {"sick": "chorobowy_ciaza", "mat": 20},
    "sprawa-war-01": {"mat": 8},
    "sprawa-wro-6": {"rate": "macierzynski_po_ustaniu"},
}


def test_eight_contest_pdfs_on_disk():
    files = sorted(SPRAWY.glob("*.pdf"))
    assert len(files) == 8


def test_juror_lists_eight_sprawy():
    ids = [item["id"] for item in list_samples() if item.get("kind") == "sprawa"]
    assert ids == list(EXPECTED)


def test_each_sprawa_calculates_through_rule_engine(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    for sample_id, expect in EXPECTED.items():
        body = calculate_sample(sample_id, params)
        assert body["missing_fields"] == [], sample_id
        assert body["profile"] is not None, sample_id
        assert body["calculation"] is not None, sample_id
        calc = body["calculation"]
        leaves = {item["leave_type"]: item for item in calc["leaves"]}
        if "combine" in expect:
            assert leaves["rodzicielski"]["calendar_weeks"] == expect["combine"]
        if "family" in expect:
            assert body["profile"]["family_path"] == expect["family"]
            assert calc["blocked"] is False
        if "mat" in expect:
            assert leaves["macierzynski"]["weeks"] == expect["mat"]
        if expect.get("supp"):
            assert "uzupelniajacy_macierzynski" in leaves
        preg = {item["code"] for item in calc["pregnancy"]}
        if "sick" in expect:
            assert expect["sick"] in preg
        if "rate" in expect:
            assert expect["rate"] in preg


def test_upload_bytes_match_catalog_without_filename(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    _meta, pdf = sample_pdf("sprawa-war-01")
    result = parse_and_calculate(pdf, params)
    assert result.profile is not None
    assert result.profile.stillbirth is True
    maternity = next(item for item in result.calculation.leaves if item.leave_type == "macierzynski")
    assert maternity.weeks == 8
