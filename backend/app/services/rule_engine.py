from typing import Any

from app.models.schemas import (
    CalculationResult,
    Claimant,
    ClaimScope,
    DocumentItem,
    EmploymentForm,
    FamilyPath,
    FilingItem,
    LeaveItem,
    ParentProfile,
    Payer,
    PregnancyItem,
    RiskItem,
)

ABOLISHED_FORMS = ("ZUR", "ZAO", "Z-3b")
WEEKS_PER_MONTH = 4.345


def _amount(base: float | None, rate: float, weeks: float | None) -> float | None:
    if base is None or weeks is None:
        return None
    return round(base * (rate / 100.0) * (weeks / WEEKS_PER_MONTH), 2)


def _pregnancy_block(profile: ParentProfile, params: dict[str, Any], waiting: int) -> list[PregnancyItem]:
    sick = params["sickness_in_pregnancy"]
    items: list[PregnancyItem] = []
    if profile.apparent_contract:
        items.append(
            PregnancyItem(
                code="pozor",
                title="Brak uprawnień — umowa dla pozoru",
                entitled=False,
                plain_language=(
                    "ZUS może uznać, że umowa albo działalność była tylko po to, "
                    "żeby dostać zasiłek. Wtedy nie ma ubezpieczenia chorobowego i nie ma zasiłków."
                ),
            )
        )
        return items
    if not profile.insured:
        items.append(
            PregnancyItem(
                code="brak_ubezpieczenia",
                title="Brak uprawnień — nie ma ubezpieczenia chorobowego",
                entitled=False,
                plain_language=(
                    "Na dzień porodu albo niezdolności do pracy nie podlegasz ubezpieczeniu chorobowemu "
                    "(np. nie zgłosiłaś dobrowolnego, skończyła się umowa). Zasiłek chorobowy nie przysługuje."
                ),
            )
        )
        return items
    if profile.insurance_days is not None and profile.insurance_days < waiting:
        items.append(
            PregnancyItem(
                code="wyczekiwanie",
                title="Brak uprawnień — za krótki staż",
                entitled=False,
                max_days=waiting,
                plain_language=(
                    f"Zasiłek chorobowy w ciąży przysługuje po {waiting} dniach ubezpieczenia. "
                    f"U Ciebie jest {profile.insurance_days} dni."
                ),
            )
        )
    else:
        items.append(
            PregnancyItem(
                code="chorobowy_ciaza",
                title="Zasiłek chorobowy w ciąży (kod B)",
                entitled=True,
                rate_percent=sick["rate_percent"],
                max_days=sick["max_days"],
                amount_pln=_amount(profile.benefit_base_pln, sick["rate_percent"], sick["max_days"] / 7),
                plain_language=(
                    f"100% podstawy, kod B na e-ZLA, maksymalnie {sick['max_days']} dni. "
                    "Pracownica: najpierw wynagrodzenie chorobowe, potem zasiłek. "
                    "Zlecenie / JDG: zasiłek od pierwszego dnia niezdolności."
                ),
            )
        )
        if profile.rehab_after_sickness:
            items.append(
                PregnancyItem(
                    code="rehabilitacyjne",
                    title="Świadczenie rehabilitacyjne",
                    entitled=True,
                    rate_percent=100,
                    plain_language=(
                        "Gdy skończy się 270 dni zasiłku, a nadal nie możesz pracować, "
                        "lekarz ZUS może przyznać świadczenie rehabilitacyjne. To nie jest urlop macierzyński."
                    ),
                )
            )
    if profile.employer_bankruptcy or profile.unlawful_dismissal:
        items.append(
            PregnancyItem(
                code="macierzynski_po_ustaniu",
                title="Zasiłek w wysokości zasiłku macierzyńskiego (do porodu)",
                entitled=True,
                rate_percent=100,
                amount_pln=_amount(profile.benefit_base_pln, 100, 4),
                plain_language=(
                    "Po utracie pracy w ciąży z powodu upadłości, likwidacji, śmierci pracodawcy "
                    "albo nielegalnego zwolnienia (wyrok) przysługuje zasiłek 100% do dnia porodu, "
                    "nawet po ustaniu ubezpieczenia."
                ),
            )
        )
    elif profile.job_ended_before_birth:
        items.append(
            PregnancyItem(
                code="utrata_pracy",
                title="Ryzyko braku zasiłku po rozwiązaniu umowy",
                entitled=False,
                plain_language=(
                    "Jeśli umowa, zlecenie albo JDG skończą się przed porodem i nie ma wyjątku "
                    "(upadłość / nielegalne zwolnienie), na dzień porodu możesz nie mieć ubezpieczenia."
                ),
            )
        )
    return items


def _filing(profile: ParentProfile, payer: Payer) -> list[FilingItem]:
    items = [
        FilingItem(
            where="ZUS albo pracodawca",
            what="Wniosek ZAM",
            deadline="Najlepiej w 21 dni po porodzie (81,5% za całość).",
            plain_language=(
                "Od 24.10.2026 jeden wniosek ZAM. ZUR, ZAO i Z-3b nie składaj — są zniesione. "
                "Wzory: zus.pl (Wzory formularzy, Zasiłki)."
            ),
        )
    ]
    if payer == Payer.employer:
        items.append(
            FilingItem(
                where="Twój pracodawca",
                what="Wniosek o urlop + ZAM u pracodawcy",
                deadline="Przed startem urlopu (macierzyński można 6 tyg. przed porodem).",
                plain_language=(
                    "Pracodawca zgłasza powyżej 20 osób, więc sam liczy i wypłaca zasiłek. "
                    "Nie idziesz z Z-3 do ZUS."
                ),
            )
        )
    elif profile.employment_form == EmploymentForm.umowa_o_prace:
        items.append(
            FilingItem(
                where="ZUS (przez pracodawcę)",
                what="ZAM + zaświadczenie Z-3",
                deadline="Z-3 składa pracodawca po Twoim wniosku o urlop.",
                plain_language="Mniejszy płatnik nie wypłaca sam — wysyła Z-3 do ZUS.",
            )
        )
    elif profile.employment_form == EmploymentForm.zlecenie:
        items.append(
            FilingItem(
                where="ZUS",
                what="ZAM + Z-3a od zleceniodawcy",
                deadline="Jak najszybciej po porodzie / starcie zasiłku.",
                plain_language="Zleceniodawca nie wypłaca — do ZUS idzie ZAM i Z-3a.",
            )
        )
    else:
        items.append(
            FilingItem(
                where="ZUS",
                what="ZAM (JDG / B2B) albo ZAS-53 przy chorobie",
                deadline="Choroba: po e-ZLA. Macierzyński: po porodzie, 21 dni na 81,5%.",
                plain_language="Składasz sama do ZUS. Przy chorobie ZAS-53. Zaległości składek mogą zablokować wypłatę.",
            )
        )
    items.append(
        FilingItem(
            where="PUE/eZUS",
            what="e-ZLA (kod B) i korespondencja",
            deadline="Lekarz wysyła e-ZLA od razu do ZUS i na profil pracodawcy.",
            plain_language="Pracownica zgłasza nieobecność pracodawcy. JDG nie pracuje i składa dokumenty do ZUS.",
        )
    )
    return items


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
    maternity_title = "Urlop macierzyński"

    if profile.stillbirth:
        maternity_weeks = 8
        maternity_title = "Urlop macierzyński (martwe urodzenie / zgon dziecka)"
    if profile.family_path == FamilyPath.adoption:
        maternity_title = "Urlop na warunkach macierzyńskiego (adopcja)"
        limit = params["adoption_age_limit_years"]
        if profile.child_age_years is not None and profile.child_age_years >= limit:
            blocked_age = True
        else:
            blocked_age = False
    elif profile.family_path == FamilyPath.foster:
        maternity_title = "Urlop na warunkach macierzyńskiego (rodzina zastępcza niezawodowa)"
        limit = (
            params["foster_deferred_school_age_limit_years"]
            if profile.school_deferred
            else params["foster_age_limit_years"]
        )
        blocked_age = profile.child_age_years is not None and profile.child_age_years >= limit
    else:
        blocked_age = False
        limit = None

    poka_yoke: list[str] = []
    blocked = False
    block_reason = None
    exception_14 = profile.mother_hospitalized or profile.mother_incapacity
    if profile.transfer_first_14_weeks_to_other_parent and not exception_14:
        blocked = True
        block_reason = (
            f"Pierwsze {mother_only} tygodni urlopu macierzyńskiego są dla matki. "
            "Nie można ich oddać drugiemu rodzicowi "
            "(wyjątki: szpital, niezdolność do samodzielnej egzystencji, zgon lub porzucenie)."
        )
        poka_yoke.append(block_reason)
    elif profile.transfer_first_14_weeks_to_other_parent and exception_14:
        poka_yoke.append(
            "Wyjątek od 14 tygodni: szpital albo niezdolność matki — ojciec może przejąć wcześniej."
        )
    if blocked_age:
        blocked = True
        block_reason = (
            f"Dziecko ma {profile.child_age_years:g} lat. Urlop na warunkach macierzyńskiego "
            f"przysługuje do {limit} r.ż."
            + (" (odroczenie szkoły)." if profile.school_deferred else ".")
        )
        poka_yoke.append(block_reason)

    poka_yoke.append(
        f"Każdy rodzic ma {non_transferable} tygodni urlopu rodzicielskiego tylko dla siebie."
    )

    leaves = [
        LeaveItem(
            leave_type="macierzynski",
            title=maternity_title,
            weeks=maternity_weeks,
            rate_percent=maternity_rate,
            transferable=False,
            mother_only=not exception_14,
            graph_node_id="swiadczenie_macierzynski",
            amount_pln=_amount(profile.benefit_base_pln, maternity_rate, maternity_weeks),
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
            amount_pln=_amount(profile.benefit_base_pln, parental_rate, parental_weeks),
            calendar_weeks=(
                round(parental_weeks / (1 - profile.combine_work_fraction), 1)
                if profile.combine_work_fraction
                else float(parental_weeks)
            ),
            plain_language=(
                f"{parental_weeks} tygodni łącznie. "
                f"{non_transferable} tygodni nieprzenoszalnych dla każdego rodzica. "
                f"Zasiłek {parental_rate:g}%."
                + (
                    f" Przy pracy na {profile.combine_work_fraction:.0%} etatu kalendarz wydłuża się "
                    f"do {parental_weeks / (1 - profile.combine_work_fraction):.1f} tyg."
                    if profile.combine_work_fraction
                    else ""
                )
                + (
                    " Rodzice mogą korzystać jednocześnie, ale 9 tygodni zostaje u każdego."
                    if profile.parental_together
                    else ""
                )
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
            amount_pln=_amount(profile.benefit_base_pln, rates["paternity"], 2),
            plain_language=(
                f"{params['paternity_calendar_days']} dni kalendarzowych "
                f"(do {params['paternity_until_child_age_months']} miesięcy życia dziecka"
                + (
                    f", przy adopcji max {params['paternity_adoption_max_age_years']} r.ż."
                    if profile.family_path == FamilyPath.adoption
                    else ""
                )
                + f"). Zasiłek {rates['paternity']:g}%."
            ),
        ),
    ]
    if profile.preterm:
        # shortcut: 8 tyg. gdy params nie podają wymiaru; upgrade: tydzień ciąży + hospitalizacja
        supp_weeks = params["supplementary_maternity"]["weeks"] or 8
        leaves.insert(
            1,
            LeaveItem(
                leave_type="uzupelniajacy_macierzynski",
                title="Uzupełniający urlop macierzyński",
                weeks=supp_weeks,
                rate_percent=rates["supplementary_maternity"],
                transferable=True,
                graph_node_id="swiadczenie_uzupelniajacy",
                amount_pln=_amount(
                    profile.benefit_base_pln, rates["supplementary_maternity"], supp_weeks
                ),
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
    if profile.apparent_contract:
        risks.append(
            RiskItem(
                code="pozorna_umowa",
                title="Umowa albo JDG dla pozoru",
                severity="block",
                plain_language="ZUS może uznać, że nie podlegasz ubezpieczeniu — wtedy nie ma zasiłków.",
                graph_node_id="ryzyko_pozorna_umowa",
            )
        )
    if profile.job_ended_before_birth:
        risks.append(
            RiskItem(
                code="brak_na_dzien_porodu",
                title="Brak ubezpieczenia na dzień porodu",
                severity="warning",
                plain_language="Koniec umowy, zlecenia albo JDG przed porodem często oznacza brak zasiłku macierzyńskiego.",
                graph_node_id="ryzyko_brak_ubezpieczenia_porod",
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

    pregnancy = _pregnancy_block(profile, params, waiting)
    if profile.claim_scope == ClaimScope.parental:
        parental_only = [item for item in leaves if item.leave_type == "rodzicielski"]
        if parental_only:
            if profile.claimant == Claimant.father:
                parental_only[0].title = "Urlop rodzicielski (ojciec)"
                parental_only[0].plain_language = (
                    f"{parental_only[0].weeks} tygodni puli rodzicielskiej. "
                    f"{non_transferable} tygodni nieprzenoszalnych dla ojca. "
                    f"Zasiłek {parental_only[0].rate_percent:g}%."
                    + (
                        f" Kwota {parental_only[0].amount_pln:.2f} zł."
                        if parental_only[0].amount_pln is not None
                        else " Brak podstawy wymiaru w dokumencie — bez kwoty."
                    )
                )
            leaves = parental_only
        pregnancy = []
        risks = [item for item in risks if item.code in {"9_tygodni_nieprzenoszalne", "termin_21_dni"}]
        explanation = ["swiadczenie_rodzicielski", "dokument_zam", "ryzyko_9_tygodni_nieprzenoszalne"]
        if combined:
            explanation.append("swiadczenie_stawka_815")
        else:
            explanation.append("swiadczenie_stawka_70")
    elif profile.claim_scope == ClaimScope.pregnancy:
        risks = [item for item in risks if item.code in {"wyczekiwanie", "zaleglosci_skladek"}]

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
        pregnancy=pregnancy,
        filing=_filing(profile, payer),
        monthly_base_pln=profile.benefit_base_pln,
        family_path=profile.family_path.value,
    )


def active_form_codes(result: CalculationResult) -> set[str]:
    return {doc.code for doc in result.documents if doc.active}
