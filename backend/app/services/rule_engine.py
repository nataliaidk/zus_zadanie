from typing import Any

from app.models.schemas import (
    CalculationResult,
    DocumentItem,
    EmploymentForm,
    LeaveItem,
    ParentProfile,
    Payer,
    RiskItem,
)

ABOLISHED_FORMS = ("ZUR", "ZAO", "Z-3b")


def _maternity_weeks(children: int, params: dict[str, Any]) -> int:
    mapping = {int(k): v for k, v in params["maternity_weeks_by_children"].items()}
    if children >= 5:
        return mapping[5]
    return mapping[children]


def _parental_weeks(children: int, za_zyciem: bool, params: dict[str, Any]) -> int:
    key_family = "multiples" if children > 1 else "single"
    if za_zyciem:
        key_family = f"za_zyciem_{key_family}"
    return params["parental_weeks"][key_family]


def _payer(profile: ParentProfile, params: dict[str, Any]) -> Payer:
    if (
        profile.employment_form == EmploymentForm.umowa_o_prace
        and profile.company_insured_above_20
    ):
        # threshold lives in params; flag already means "above N"
        _ = params["employer_pays_if_insured_above"]
        return Payer.employer
    return Payer.zus


def _combined_rate(profile: ParentProfile, params: dict[str, Any]) -> bool:
    deadline = params["combined_rate_request_deadline_days"]
    return (
        profile.request_days_after_birth is not None
        and profile.request_days_after_birth <= deadline
    )


def calculate(profile: ParentProfile, params: dict[str, Any]) -> CalculationResult:
    waiting = params["waiting_period_days"][profile.employment_form.value]
    rates = params["rates_percent"]
    combined = _combined_rate(profile, params)
    maternity_rate = rates["combined_if_request_within_deadline"] if combined else rates["maternity"]
    parental_rate = rates["combined_if_request_within_deadline"] if combined else rates["parental"]
    payer = _payer(profile, params)
    maternity_weeks = _maternity_weeks(profile.number_of_children, params)
    parental_weeks = _parental_weeks(
        profile.number_of_children, profile.za_zyciem_certificate, params
    )
    non_transferable = params["non_transferable_weeks_per_parent"]
    mother_only = params["mother_only_weeks"]

    poka_yoke: list[str] = []
    blocked = False
    block_reason = None
    if profile.transfer_first_14_weeks_to_other_parent:
        blocked = True
        block_reason = (
            f"Pierwsze {mother_only} tygodni urlopu macierzyńskiego są dla matki. "
            "Nie można ich oddać drugiemu rodzicowi "
            "(wyjątki: szpital, niezdolność do samodzielnej egzystencji, zgon lub porzucenie)."
        )
        poka_yoke.append(block_reason)

    poka_yoke.append(
        f"Każdy rodzic ma {non_transferable} tygodni urlopu rodzicielskiego tylko dla siebie."
    )

    leaves = [
        LeaveItem(
            leave_type="macierzynski",
            title="Urlop macierzyński",
            weeks=maternity_weeks,
            rate_percent=maternity_rate,
            transferable=False,
            mother_only=True,
            graph_node_id="swiadczenie_macierzynski",
            plain_language=(
                f"{maternity_weeks} tygodni. Pierwsze {mother_only} tygodni tylko dla matki. "
                f"Zasiłek {maternity_rate:g}%."
            ),
        ),
        LeaveItem(
            leave_type="rodzicielski",
            title="Urlop rodzicielski",
            weeks=parental_weeks,
            rate_percent=parental_rate,
            transferable=True,
            graph_node_id="swiadczenie_rodzicielski",
            plain_language=(
                f"{parental_weeks} tygodni łącznie. "
                f"{non_transferable} tygodni nieprzenoszalnych dla każdego rodzica. "
                f"Zasiłek {parental_rate:g}%."
            ),
        ),
        LeaveItem(
            leave_type="ojcowski",
            title="Urlop ojcowski",
            days=params["paternity_calendar_days"],
            weeks=2,
            rate_percent=rates["paternity"],
            transferable=False,
            graph_node_id="swiadczenie_ojcowski",
            plain_language=(
                f"{params['paternity_calendar_days']} dni kalendarzowych "
                f"(do {params['paternity_until_child_age_months']} miesięcy życia dziecka). "
                f"Zasiłek {rates['paternity']:g}%."
            ),
        ),
    ]
    if profile.preterm:
        leaves.insert(
            1,
            LeaveItem(
                leave_type="uzupelniajacy_macierzynski",
                title="Uzupełniający urlop macierzyński",
                weeks=params["supplementary_maternity"]["weeks"],
                rate_percent=rates["supplementary_maternity"],
                transferable=True,
                graph_node_id="swiadczenie_uzupelniajacy",
                plain_language=(
                    "Jednorazowo, od razu po macierzyńskim, zasiłek 100%. "
                    + params["supplementary_maternity"]["note"]
                ),
            ),
        )

    forms = params["forms"]
    documents = [
        DocumentItem(
            code=forms["active_parental_application"],
            title="Wniosek ZAM",
            active=True,
            plain_language="Jeden wniosek o zasiłek macierzyński. Zastępuje ZUR, ZAO i Z-3b.",
            graph_node_id="dokument_zam",
        )
    ]
    if payer == Payer.zus and profile.employment_form == EmploymentForm.umowa_o_prace:
        documents.append(
            DocumentItem(
                code=forms["employee_to_zus"],
                title="Zaświadczenie Z-3",
                active=True,
                plain_language="Pracodawca przekazuje Z-3 do ZUS, bo sam nie wypłaca zasiłku.",
                graph_node_id="dokument_z3",
            )
        )
    if payer == Payer.zus and profile.employment_form == EmploymentForm.zlecenie:
        documents.append(
            DocumentItem(
                code=forms["contractor_to_zus"],
                title="Zaświadczenie Z-3a",
                active=True,
                plain_language="Zleceniodawca przekazuje Z-3a do ZUS.",
                graph_node_id="dokument_z3a",
            )
        )
    if profile.za_zyciem_certificate:
        documents.append(
            DocumentItem(
                code="ZA_ZYCIEM",
                title="Zaświadczenie „Za życiem”",
                active=True,
                plain_language="Potrzebne do dłuższego urlopu rodzicielskiego.",
                graph_node_id="dokument_za_zyciem",
            )
        )
    for code in forms["abolished"]:
        documents.append(
            DocumentItem(
                code=code,
                title=f"{code} — zniesiony",
                active=False,
                replaced_by=forms["active_parental_application"],
                plain_language=f"{code} nie obowiązuje od 24 października 2026. Złóż ZAM.",
                graph_node_id="dokument_zniesione_zur_zao_z3b",
            )
        )

    risks: list[RiskItem] = []
    wait_node = "ryzyko_wyczekiwanie_30" if waiting == 30 else "ryzyko_wyczekiwanie_90"
    risks.append(
        RiskItem(
            code="wyczekiwanie",
            title=f"Okres wyczekiwania {waiting} dni",
            severity="info",
            plain_language=(
                f"Zasiłek chorobowy w ciąży przysługuje po {waiting} dniach ubezpieczenia "
                f"({profile.employment_form.value})."
            ),
            graph_node_id=wait_node,
        )
    )
    risks.append(
        RiskItem(
            code="14_tygodni_matka",
            title="Pierwsze 14 tygodni tylko dla matki",
            severity="block" if blocked else "info",
            plain_language=f"Pierwsze {mother_only} tygodni macierzyńskiego nie oddasz partnerowi.",
            graph_node_id="ryzyko_14_tygodni_matka",
        )
    )
    risks.append(
        RiskItem(
            code="9_tygodni_nieprzenoszalne",
            title="9 tygodni nieprzenoszalnych",
            severity="info",
            plain_language=f"Każdy rodzic ma {non_transferable} tygodni tylko dla siebie.",
            graph_node_id="ryzyko_9_tygodni_nieprzenoszalne",
        )
    )
    if not combined:
        risks.append(
            RiskItem(
                code="termin_21_dni",
                title="Stawka 81,5% tylko do 21 dni po porodzie",
                severity="info",
                plain_language=(
                    "Jeśli matka złoży wniosek nie później niż 21 dni po porodzie, "
                    "zasiłek za macierzyński i rodzicielski wynosi 81,5% za całość."
                ),
                graph_node_id="ryzyko_termin_wniosku_21",
            )
        )
    if profile.part_time:
        risks.append(
            RiskItem(
                code="niepelnny_etat",
                title="Część etatu a kwota zasiłku",
                severity="warning",
                plain_language="Urlop trwa tyle samo, ale kwota może być niższa.",
                graph_node_id="ryzyko_podstawa_niepelnny_etat",
            )
        )
    if profile.b2b_arrears:
        risks.append(
            RiskItem(
                code="zaleglosci_skladek",
                title="Zaległości składek",
                severity="block",
                plain_language="ZUS może odmówić zasiłku, dopóki składki nie są opłacone.",
                graph_node_id="ryzyko_zaleglosci_b2b",
            )
        )

    explanation = [
        "swiadczenie_macierzynski",
        "swiadczenie_rodzicielski",
        "dokument_zam",
        wait_node,
        "ryzyko_14_tygodni_matka",
        "ryzyko_9_tygodni_nieprzenoszalne",
    ]
    if combined:
        explanation.append("swiadczenie_stawka_815")
    else:
        explanation.extend(["swiadczenie_stawka_100", "swiadczenie_stawka_70"])

    return CalculationResult(
        legal_as_of=params["legal_as_of"],
        waiting_period_days=waiting,
        payer=payer,
        combined_rate_applied=combined,
        leaves=leaves,
        documents=documents,
        risks=risks,
        blocked=blocked,
        block_reason=block_reason,
        explanation_node_ids=explanation,
        poka_yoke=poka_yoke,
    )


def active_form_codes(result: CalculationResult) -> set[str]:
    return {doc.code for doc in result.documents if doc.active}
