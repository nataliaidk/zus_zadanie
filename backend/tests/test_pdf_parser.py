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


def test_upload_filename_pregnancy_sickness_without_catalog(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    pdf = make_pdf(["skan bez warstwy tekstu"])
    result = parse_and_calculate(
        pdf,
        params,
        source_name="Zuzanna Le_zas. chorobowy w ciąży.pdf",
    )
    assert result.missing_fields == []
    assert result.profile is not None
    assert result.calculation is not None
    assert result.document_code == "ZAS-53"
    assert result.extraction_method == "nazwa"
    sick = next(item for item in result.calculation.pregnancy if item.code == "chorobowy_ciaza")
    assert sick.entitled is True
    assert sick.rate_percent == 100
    assert "kod B" in result.plain_language


def test_contest_filenames_calculate_without_hash(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    pdf = make_pdf(["skan"])
    names = {
        "Agnieszka_Wa_zas. mac. laczenie urlopu rodzicielskiego z praca.pdf": "combine",
        "Agnieszka_War_zas. macierzynski - przyjecie dziecka na wychowanie.pdf": "foster",
        "Alicja_Ta_zasilek chorobowy i macierzynski.pdf": "sick_mat",
        "Anna_Ko_zas. chorobowy w ci__y.pdf": "preg",
        "Anna_Lu_zas. mac. uzupelniajacego url. mac. rodzicielskiego.pdf": "supp",
        "Anna_No_zas. chorobowy i macierzynski.pdf": "sick_mat",
        "Anna_War_zas. macierzynski martwe urodzenie.pdf": "still",
        "Anna_Wro_zas. w wysokosci zasilku macierzynskiego.pdf": "rate",
    }
    for name, kind in names.items():
        result = parse_and_calculate(pdf, params, source_name=name)
        assert result.profile is not None, name
        assert result.calculation is not None, name
        assert result.missing_fields == [], name
        if kind == "combine":
            parental = next(item for item in result.calculation.leaves if item.leave_type == "rodzicielski")
            assert parental.calendar_weeks == 82.0
        elif kind == "foster":
            assert result.profile.family_path.value == "foster"
        elif kind == "preg":
            assert result.document_code == "ZAS-53"
            assert any(item.code == "chorobowy_ciaza" for item in result.calculation.pregnancy)
        elif kind == "supp":
            assert any(item.leave_type == "uzupelniajacy_macierzynski" for item in result.calculation.leaves)
        elif kind == "still":
            mat = next(item for item in result.calculation.leaves if item.leave_type == "macierzynski")
            assert mat.weeks == 8
        elif kind == "rate":
            assert any(item.code == "macierzynski_po_ustaniu" for item in result.calculation.pregnancy)


def test_wojciech_parental_uses_pdf_base_not_kod_b(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    pdf = make_pdf(
        [
            "ZAM",
            "Wniosek o zasilek macierzynski za okres urlopu rodzicielskiego",
            "Data porodu: 01.03.2026",
            "Liczba dzieci: 1",
            "umowa o prace",
            "Podstawa wymiaru: 6120,50 zl",
            "Liczba ubezpieczonych: 8",
        ]
    )
    result = parse_and_calculate(
        pdf,
        params,
        source_name="Wojciech Lu_4_zas. mac. za okres urlopu rodzicielskiego.pdf",
    )
    assert result.missing_fields == []
    assert result.profile is not None
    assert result.profile.claimant.value == "father"
    assert result.profile.claim_scope.value == "parental"
    assert result.profile.benefit_base_pln == 6120.5
    assert [item.leave_type for item in result.calculation.leaves] == ["rodzicielski"]
    parental = result.calculation.leaves[0]
    assert parental.weeks == 41
    assert parental.rate_percent == 70.0
    assert parental.amount_pln is not None and parental.amount_pln > 0
    assert result.calculation.payer.value == "ZUS"
    assert result.calculation.monthly_base_pln == 6120.5
    assert not any(item.code == "chorobowy_ciaza" for item in result.calculation.pregnancy)
    assert "kod B" not in result.plain_language
    assert "6120.50" in result.plain_language
    assert "ojca" in result.plain_language.lower() or "ojciec" in result.plain_language.lower()


def test_unrelated_filename_still_needs_fields(params, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    result = parse_and_calculate(make_pdf(["skan bez warstwy tekstu"]), params, source_name="faktura.pdf")
    assert result.profile is None
    assert "employment_form" in result.missing_fields


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
