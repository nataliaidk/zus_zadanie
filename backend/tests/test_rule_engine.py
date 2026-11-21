from datetime import date

import pytest

from app.models.schemas import EmploymentForm, ParentProfile, Payer
from app.services.rule_engine import ABOLISHED_FORMS, active_form_codes, calculate


def _profile(**overrides) -> ParentProfile:
    data = {
        "employment_form": EmploymentForm.umowa_o_prace,
        "company_insured_above_20": False,
        "birth_date": date(2026, 11, 1),
        "number_of_children": 1,
        "preterm": False,
        "za_zyciem_certificate": False,
        "part_time": False,
        "b2b_arrears": False,
        "request_days_after_birth": None,
        "transfer_first_14_weeks_to_other_parent": False,
    }
    data.update(overrides)
    return ParentProfile(**data)


def _leave(result, leave_type: str):
    return next(item for item in result.leaves if item.leave_type == leave_type)


def test_waiting_period_30_employment_contract(params):
    result = calculate(_profile(employment_form=EmploymentForm.umowa_o_prace), params)
    assert result.waiting_period_days == 30


@pytest.mark.parametrize("form", [EmploymentForm.zlecenie, EmploymentForm.jdg, EmploymentForm.b2b])
def test_waiting_period_90_voluntary(params, form):
    result = calculate(_profile(employment_form=form), params)
    assert result.waiting_period_days == 90


def test_maternity_20_weeks_one_child(params):
    result = calculate(_profile(number_of_children=1), params)
    assert _leave(result, "macierzynski").weeks == 20


def test_maternity_31_weeks_twins(params):
    result = calculate(_profile(number_of_children=2), params)
    assert _leave(result, "macierzynski").weeks == 31


def test_maternity_37_weeks_five_children(params):
    result = calculate(_profile(number_of_children=5), params)
    assert _leave(result, "macierzynski").weeks == 37


def test_non_transferable_9_weeks_each_parent(params):
    result = calculate(_profile(), params)
    parental = _leave(result, "rodzicielski")
    assert params["non_transferable_weeks_per_parent"] == 9
    assert "9 tygodni nieprzenoszalnych" in parental.plain_language
    assert any(risk.code == "9_tygodni_nieprzenoszalne" for risk in result.risks)


def test_first_14_weeks_mother_only_poka_yoke(params):
    result = calculate(_profile(transfer_first_14_weeks_to_other_parent=True), params)
    maternity = _leave(result, "macierzynski")
    assert maternity.mother_only is True
    assert result.blocked is True
    assert result.block_reason is not None
    assert "14" in result.block_reason
    assert any("14" in msg for msg in result.poka_yoke)


def test_combined_rate_815_when_request_within_21_days(params):
    result = calculate(_profile(request_days_after_birth=21), params)
    assert result.combined_rate_applied is True
    assert _leave(result, "macierzynski").rate_percent == 81.5
    assert _leave(result, "rodzicielski").rate_percent == 81.5
    assert _leave(result, "ojcowski").rate_percent == 100.0


def test_split_rates_when_request_after_21_days(params):
    result = calculate(_profile(request_days_after_birth=22), params)
    assert result.combined_rate_applied is False
    assert _leave(result, "macierzynski").rate_percent == 100.0
    assert _leave(result, "rodzicielski").rate_percent == 70.0


def test_zam_replaces_abolished_forms(params):
    result = calculate(_profile(), params)
    active = active_form_codes(result)
    assert "ZAM" in active
    for code in ABOLISHED_FORMS:
        assert code not in active
        abolished = next(doc for doc in result.documents if doc.code == code)
        assert abolished.active is False
        assert abolished.replaced_by == "ZAM"


def test_payer_employer_when_large_company(params):
    result = calculate(_profile(company_insured_above_20=True), params)
    assert result.payer == Payer.employer
    assert "Z-3" not in active_form_codes(result)


def test_payer_zus_small_employer_emits_z3(params):
    result = calculate(_profile(company_insured_above_20=False), params)
    assert result.payer == Payer.zus
    assert "Z-3" in active_form_codes(result)


def test_za_zyciem_extends_parental_leave(params):
    one = calculate(_profile(za_zyciem_certificate=True, number_of_children=1), params)
    many = calculate(_profile(za_zyciem_certificate=True, number_of_children=2), params)
    assert _leave(one, "rodzicielski").weeks == 65
    assert _leave(many, "rodzicielski").weeks == 67


def test_preterm_adds_supplementary_leave_at_100(params):
    result = calculate(_profile(preterm=True), params)
    extra = _leave(result, "uzupelniajacy_macierzynski")
    assert extra.rate_percent == 100.0


def test_b2b_arrears_risk(params):
    result = calculate(
        _profile(employment_form=EmploymentForm.b2b, b2b_arrears=True),
        params,
    )
    assert any(risk.code == "zaleglosci_skladek" and risk.severity == "block" for risk in result.risks)
