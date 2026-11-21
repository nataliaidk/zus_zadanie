from datetime import date

from app.models.schemas import EmploymentForm, FamilyPath, ParentProfile
from app.services.rule_engine import calculate


def _profile(**overrides) -> ParentProfile:
    data = {
        "employment_form": EmploymentForm.umowa_o_prace,
        "company_insured_above_20": False,
        "birth_date": date(2026, 11, 1),
        "number_of_children": 1,
        "benefit_base_pln": 5200,
    }
    data.update(overrides)
    return ParentProfile(**data)


def test_pregnancy_sickness_code_b(params):
    result = calculate(_profile(), params)
    codes = {item.code for item in result.pregnancy}
    assert "chorobowy_ciaza" in codes
    sick = next(item for item in result.pregnancy if item.code == "chorobowy_ciaza")
    assert sick.entitled is True
    assert sick.rate_percent == 100
    assert sick.max_days == 270


def test_no_entitlement_uninsured(params):
    result = calculate(_profile(insured=False), params)
    assert result.pregnancy[0].entitled is False
    assert "nie przysługuje" in result.pregnancy[0].plain_language.lower()


def test_maternity_rate_sickness_after_bankruptcy(params):
    result = calculate(_profile(employer_bankruptcy=True), params)
    assert any(item.code == "macierzynski_po_ustaniu" for item in result.pregnancy)


def test_stillbirth_eight_weeks(params):
    result = calculate(_profile(stillbirth=True), params)
    mat = next(item for item in result.leaves if item.leave_type == "macierzynski")
    assert mat.weeks == 8


def test_adoption_too_old_blocked(params):
    result = calculate(
        _profile(family_path=FamilyPath.adoption, child_age_years=14),
        params,
    )
    assert result.blocked is True
    assert "14" in (result.block_reason or "")


def test_foster_age_limit(params):
    result = calculate(
        _profile(family_path=FamilyPath.foster, child_age_years=8),
        params,
    )
    assert result.blocked is True
    ok = calculate(
        _profile(family_path=FamilyPath.foster, child_age_years=6),
        params,
    )
    assert ok.blocked is False
    assert "zastępcza" in ok.leaves[0].title


def test_amount_from_base(params):
    result = calculate(_profile(request_days_after_birth=0, benefit_base_pln=5200), params)
    mat = next(item for item in result.leaves if item.leave_type == "macierzynski")
    assert mat.amount_pln is not None
    assert mat.amount_pln > 0
    assert result.monthly_base_pln == 5200


def test_half_time_calendar_stretch(params):
    result = calculate(_profile(combine_work_fraction=0.5), params)
    parental = next(item for item in result.leaves if item.leave_type == "rodzicielski")
    assert parental.calendar_weeks == 82.0


def test_hospital_exception_allows_early_father(params):
    result = calculate(
        _profile(transfer_first_14_weeks_to_other_parent=True, mother_hospitalized=True),
        params,
    )
    assert result.blocked is False


def test_filing_mentions_zam(params):
    result = calculate(_profile(), params)
    assert any("ZAM" in item.what for item in result.filing)
