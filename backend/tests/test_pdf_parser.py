from app.services.pdf_parser import detect_document_type, parse_and_calculate, regex_extract
from tests.pdf_fixtures import INSURANCE_LINES, Z3_LINES, ZAM_LINES, ZUR_LINES, make_pdf


def test_regex_handles_spaced_zam_and_diacritic_dates():
    text = "\n".join(
        [
            "W N I O S E K  Z A M",
            "Data porodu 01 11 2026",
            "Data zlozenia wniosku 10.11.2026",
            "Liczba dzieci: 1",
            "umowa o pracę",
            "Zaświadczenie za życiem: nie",
        ]
    )
    fields = regex_extract(text)
    assert detect_document_type(text) == ("zam", "ZAM")
    assert fields["birth_date"].isoformat() == "2026-11-01"
    assert fields["number_of_children"] == 1
    assert fields["employment_form"].value == "umowa_o_prace"


def test_filename_hint_stillbirth_and_foster(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    pdf = make_pdf(
        [
            "ZAM",
            "Data porodu: 01.03.2026",
            "Liczba dzieci: 1",
            "umowa o prace",
            "martwe urodzenie",
        ]
    )
    still = parse_and_calculate(pdf, params, source_name="Anna_War_01_zas._macierzy_ski__martwe_urodzenie.pdf")
    assert still.profile is not None
    assert still.profile.stillbirth is True
    assert next(item.weeks for item in still.calculation.leaves if item.leave_type == "macierzynski") == 8

    foster_pdf = make_pdf(
        [
            "ZAM",
            "Data porodu: 01.06.2024",
            "Liczba dzieci: 1",
            "umowa o prace",
            "przyjecie dziecka na wychowanie",
        ]
    )
    foster = parse_and_calculate(
        foster_pdf,
        params,
        source_name="Agnieszka_War_02_zas._macierzy_ski_-_przyj_cie_dziecka_na_wychowanie.pdf",
    )
    assert foster.profile is not None
    assert foster.profile.family_path.value == "foster"


def test_regex_zam_maps_to_profile_fields():
    text = "\n".join(ZAM_LINES)
    fields = regex_extract(text)
    assert detect_document_type(text) == ("zam", "ZAM")
    assert fields["employment_form"].value == "umowa_o_prace"
    assert fields["number_of_children"] == 1
    assert fields["request_days_after_birth"] == 9
    assert fields["za_zyciem_certificate"] is False
    assert fields["preterm"] is False


def test_pdf_zam_calculate_without_llm(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = parse_and_calculate(make_pdf(ZAM_LINES), params)
    assert result.extraction_method == "regex"
    assert result.document_code == "ZAM"
    assert result.profile is not None
    assert result.calculation is not None
    assert result.calculation.waiting_period_days == 30
    assert result.calculation.combined_rate_applied is True
    assert not any(doc.code in {"ZUR", "ZAO", "Z-3b"} and doc.active for doc in result.calculation.documents)


def test_pdf_z3_small_payer_and_twins(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = parse_and_calculate(make_pdf(Z3_LINES), params)
    assert result.document_code == "Z-3"
    assert result.profile is not None
    assert result.profile.number_of_children == 2
    assert result.profile.part_time is True
    assert result.profile.company_insured_above_20 is False
    assert result.insurance.payer_hint == "ZUS"
    assert result.insurance.waiting_period_met is True
    maternity = next(item for item in result.calculation.leaves if item.leave_type == "macierzynski")
    assert maternity.weeks == 31


def test_pdf_insurance_certificate_waiting_period(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = parse_and_calculate(make_pdf(INSURANCE_LINES), params)
    assert result.document_type == "insurance_certificate"
    assert result.insurance.covered_on_birth is True
    assert result.insurance.waiting_period_days == 30
    assert result.insurance.waiting_period_met is True
    assert result.calculation is not None


def test_pdf_zur_abolished_not_active(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = parse_and_calculate(make_pdf(ZUR_LINES), params)
    assert result.document_code == "ZUR"
    assert result.abolished_form_warning is not None
    assert "ZAM" in result.abolished_form_warning
    if result.calculation:
        assert not any(doc.code == "ZUR" and doc.active for doc in result.calculation.documents)
