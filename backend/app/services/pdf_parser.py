"""Parse ZUS contest PDFs (ZAM, Z-3, insurance certificates) into a ParentProfile.

Regex always runs. LLM fills gaps only when an API key is present. Amounts stay
in the deterministic rule engine.
"""

from __future__ import annotations

import io
import re
from datetime import date, datetime
from typing import Any, Optional

import pdfplumber

from app.models.schemas import (
    EmploymentForm,
    InsuranceVerification,
    ParentProfile,
    PdfCalculateResponse,
)
from app.services import llm
from app.services.rule_engine import calculate

ABOLISHED = {"ZUR": "ZAM", "ZAO": "ZAM", "Z-3b": "ZAM"}

_DATE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})"


def extract_text(pdf_bytes: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def detect_document_type(text: str) -> tuple[str, str]:
    upper = text.upper()
    if re.search(r"\bZUR\b", upper):
        return "abolished", "ZUR"
    if re.search(r"\bZAO\b", upper):
        return "abolished", "ZAO"
    if re.search(r"Z-?3B\b", upper):
        return "abolished", "Z-3b"
    if re.search(r"\bZAM\b", upper) or re.search(r"wniosek o zasi[lł]ek macierzy", text, re.I):
        return "zam", "ZAM"
    if re.search(r"Z-?3A\b", upper):
        return "z3a", "Z-3a"
    if re.search(r"Z-?3\b", upper) or re.search(r"za[sś]wiadczenie p[lł]atnika", text, re.I):
        return "z3", "Z-3"
    if re.search(
        r"po[sś]wiadczenie ubezpieczenia|podlegani[ae]\s+ubezpieczeniu chorob",
        text,
        re.I,
    ):
        return "insurance_certificate", "UBEZP"
    return "unknown", "UNKNOWN"


def _parse_date(raw: str) -> Optional[date]:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _first_date(text: str, label: str) -> Optional[date]:
    match = re.search(label + r"[:\s]+" + _DATE, text, re.I)
    return _parse_date(match.group(1)) if match else None


def _yes_no(text: str, label: str) -> Optional[bool]:
    match = re.search(r"(?:" + label + r")[:\s]+(tak|nie|yes|no)\b", text, re.I)
    if not match:
        return None
    return match.group(1).lower() in {"tak", "yes"}


def regex_extract(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    birth = _first_date(text, r"data\s+(?:porodu|urodzenia(?:\s+dziecka)?)")
    if birth:
        fields["birth_date"] = birth
    filed = _first_date(text, r"data\s+(?:z[lł]o[zż]enia\s+wniosku|wniosku)")
    if filed and birth:
        fields["request_days_after_birth"] = abs((filed - birth).days)
    elif filed:
        fields["application_date"] = filed

    children = re.search(
        r"liczba\s+dzieci(?:\s+urodzonych(?:\s+przy\s+jednym\s+porodzie)?)?[:\s]+(\d+)",
        text,
        re.I,
    )
    if not children:
        children = re.search(r"urodzeni[eau]\s+(\d+)\s+dziec", text, re.I)
    if children:
        fields["number_of_children"] = int(children.group(1))

    if re.search(r"umow[ay]\s+o\s+prac", text, re.I):
        fields["employment_form"] = EmploymentForm.umowa_o_prace
    elif re.search(r"\bb2b\b", text, re.I):
        fields["employment_form"] = EmploymentForm.b2b
    elif re.search(r"zlecen", text, re.I):
        fields["employment_form"] = EmploymentForm.zlecenie
    elif re.search(r"dzia[lł]alno[sś][cć]|jdg|pozarolnicz", text, re.I):
        fields["employment_form"] = EmploymentForm.jdg

    insured = re.search(
        r"liczba\s+ubezpieczonych[^\n]{0,80}:\s*(\d+)",
        text,
        re.I,
    )
    if insured:
        count = int(insured.group(1))
        fields["insured_count"] = count
        fields["company_insured_above_20"] = count > 20

    za = _yes_no(text, r"(?:za[sś]wiadczenie\s+)?za\s+[zż]yciem")
    if za is None and re.search(r"za\s+[zż]yciem", text, re.I):
        za = not re.search(r"za\s+[zż]yciem[:\s]+nie", text, re.I)
    if za is not None:
        fields["za_zyciem_certificate"] = za

    if re.search(r"(wcze[sś]niak|por[oó]d przedwczesny)[:\s]+nie", text, re.I):
        fields["preterm"] = False
    elif re.search(r"(wcze[sś]niak|por[oó]d przedwczesny)[:\s]+tak", text, re.I):
        fields["preterm"] = True
    elif re.search(r"hospitalizac(?:ja|ji)\s+po\s+porodzie", text, re.I):
        fields["preterm"] = True

    if re.search(r"niepe[lł]n[ya]\s+etat|wymiar[^.\n]{0,40}(1/2|1/4|0[,.]5)", text, re.I):
        fields["part_time"] = True
    elif re.search(r"pe[lł]n[ya]\s+etat|wymiar[^.\n]{0,20}1/1", text, re.I):
        fields["part_time"] = False

    arrears = _yes_no(text, r"zaleg[lł]o[sś]ci(?:\s+sk[lł]adek)?|zad[lł]u[zż]enie")
    if arrears is not None:
        fields["b2b_arrears"] = arrears

    start = _first_date(text, r"(?:podleganie od|ubezpieczenie od|okres od)")
    if start:
        fields["insurance_start"] = start

    if re.search(r"nie podlega(?:\s+ubezpieczeniu)?", text, re.I):
        fields["covered_on_birth"] = False
    elif re.search(r"podlega ubezpieczeniu chorob", text, re.I):
        fields["covered_on_birth"] = True

    return fields


def llm_extract(text: str) -> dict[str, Any]:
    payload = llm.complete_json(
        "Extract fields from this Polish ZUS form. Return JSON only with keys: "
        "employment_form (umowa_o_prace|zlecenie|jdg|b2b), "
        "company_insured_above_20 (bool), birth_date (YYYY-MM-DD), "
        "number_of_children (int), preterm (bool), za_zyciem_certificate (bool), "
        "part_time (bool), b2b_arrears (bool), request_days_after_birth (int), "
        "insurance_start (YYYY-MM-DD), insured_count (int), covered_on_birth (bool). "
        "Omit unknown keys. Do not return benefit amounts or leave lengths.\n\n"
        f"{text[:8000]}",
        system="You extract structured fields from ZUS PDFs. Never invent legal amounts.",
    )
    if not payload:
        return {}
    cleaned: dict[str, Any] = {}
    if payload.get("employment_form") in {e.value for e in EmploymentForm}:
        cleaned["employment_form"] = EmploymentForm(payload["employment_form"])
    for key in (
        "company_insured_above_20",
        "preterm",
        "za_zyciem_certificate",
        "part_time",
        "b2b_arrears",
        "covered_on_birth",
    ):
        if isinstance(payload.get(key), bool):
            cleaned[key] = payload[key]
    if isinstance(payload.get("number_of_children"), int) and payload["number_of_children"] >= 1:
        cleaned["number_of_children"] = payload["number_of_children"]
    if isinstance(payload.get("request_days_after_birth"), int) and payload["request_days_after_birth"] >= 0:
        cleaned["request_days_after_birth"] = payload["request_days_after_birth"]
    if isinstance(payload.get("insured_count"), int):
        cleaned["insured_count"] = payload["insured_count"]
        cleaned.setdefault("company_insured_above_20", payload["insured_count"] > 20)
    for date_key in ("birth_date", "insurance_start"):
        raw = payload.get(date_key)
        if isinstance(raw, str):
            parsed = _parse_date(raw)
            if parsed:
                cleaned[date_key] = parsed
    return cleaned


def merge_fields(regex_fields: dict[str, Any], llm_fields: dict[str, Any]) -> tuple[dict[str, Any], str]:
    merged = dict(llm_fields)
    merged.update(regex_fields)  # regex wins on overlap
    method = "regex+llm" if llm_fields else "regex"
    return merged, method


PROFILE_REQUIRED = ("employment_form", "birth_date", "number_of_children")


def to_profile(fields: dict[str, Any]) -> tuple[Optional[ParentProfile], list[str]]:
    missing = [name for name in PROFILE_REQUIRED if name not in fields]
    if missing:
        return None, missing
    return (
        ParentProfile(
            employment_form=fields["employment_form"],
            company_insured_above_20=bool(fields.get("company_insured_above_20", False)),
            birth_date=fields["birth_date"],
            number_of_children=fields["number_of_children"],
            preterm=bool(fields.get("preterm", False)),
            za_zyciem_certificate=bool(fields.get("za_zyciem_certificate", False)),
            part_time=bool(fields.get("part_time", False)),
            b2b_arrears=bool(fields.get("b2b_arrears", False)),
            request_days_after_birth=fields.get("request_days_after_birth"),
        ),
        [],
    )


def verify_insurance(fields: dict[str, Any], params: dict[str, Any]) -> InsuranceVerification:
    notes: list[str] = []
    graph_ids: list[str] = []
    employment: Optional[EmploymentForm] = fields.get("employment_form")
    waiting = None
    if employment is not None:
        waiting = params["waiting_period_days"][employment.value]
        graph_ids.append(
            "ryzyko_wyczekiwanie_30" if waiting == 30 else "ryzyko_wyczekiwanie_90"
        )
    start: Optional[date] = fields.get("insurance_start")
    birth: Optional[date] = fields.get("birth_date")
    met = None
    if start and birth and waiting is not None:
        met = (birth - start).days >= waiting
        notes.append(
            f"Od początku ubezpieczenia ({start.isoformat()}) do porodu "
            f"({birth.isoformat()}) minęło {(birth - start).days} dni. "
            f"Potrzeba {waiting} dni wyczekiwania."
        )
        if not met:
            notes.append("Okres wyczekiwania może nie być spełniony — zasiłek chorobowy w ciąży może nie przysługiwać.")
    covered = fields.get("covered_on_birth")
    if covered is False:
        notes.append("Dokument wskazuje, że w dniu porodu nie ma ubezpieczenia chorobowego.")
        graph_ids.append("status_zaleglosci_skladek")
    elif covered is True:
        notes.append("Dokument potwierdza podleganie ubezpieczeniu chorobowemu.")

    payer_hint = None
    if "company_insured_above_20" in fields:
        if fields["company_insured_above_20"]:
            payer_hint = "pracodawca"
            graph_ids.append("status_duzy_platnik")
            notes.append("Płatnik zgłaszał powyżej 20 ubezpieczonych — zasiłek wypłaca pracodawca.")
        else:
            payer_hint = "ZUS"
            graph_ids.append("status_maly_platnik")
            notes.append("Mniejszy płatnik — zasiłek wypłaca ZUS.")

    arrears = fields.get("b2b_arrears")
    if arrears:
        graph_ids.append("ryzyko_zaleglosci_b2b")
        notes.append("Są zaległości składek. ZUS może odmówić zasiłku.")

    if not notes:
        notes.append("Za mało danych na pełną weryfikację ubezpieczenia. Regex nie znalazł daty podlegania albo tytułu.")

    return InsuranceVerification(
        covered_on_birth=covered,
        waiting_period_days=waiting,
        waiting_period_met=met,
        insurance_start=start,
        payer_hint=payer_hint,
        arrears=arrears,
        notes=notes,
        graph_node_ids=list(dict.fromkeys(graph_ids)),
    )


def parse_and_calculate(pdf_bytes: bytes, params: dict[str, Any]) -> PdfCalculateResponse:
    text = extract_text(pdf_bytes)
    doc_type, code = detect_document_type(text)
    regex_fields = regex_extract(text)
    llm_fields = llm_extract(text) if llm.llm_configured() else {}
    fields, method = merge_fields(regex_fields, llm_fields)
    profile, missing = to_profile(fields)
    insurance = verify_insurance(fields, params)

    warning = None
    if doc_type == "abolished":
        warning = (
            f"{code} nie obowiązuje od 24 października 2026 r. "
            f"Zastępuje go {ABOLISHED[code]}. Nie składaj {code} jako aktywnego wniosku."
        )

    calculation = calculate(profile, params) if profile else None
    serializable = {
        key: (value.isoformat() if isinstance(value, date) else value.value if isinstance(value, EmploymentForm) else value)
        for key, value in fields.items()
    }
    if profile and calculation:
        summary = (
            f"Rozpoznano {code}. Ubezpieczenie: {insurance.notes[0]} "
            f"Urlop macierzyński: {next(item.weeks for item in calculation.leaves if item.leave_type == 'macierzynski')} tyg."
        )
    else:
        summary = f"Rozpoznano {code}. Brakuje pól do kalkulacji: {', '.join(missing) or 'brak'}."
        if warning:
            summary = warning + " " + summary

    return PdfCalculateResponse(
        document_type=doc_type,
        document_code=code,
        extraction_method=method,
        profile=profile,
        missing_fields=missing,
        extracted_fields=serializable,
        insurance=insurance,
        calculation=calculation,
        abolished_form_warning=warning,
        plain_language=summary,
    )
