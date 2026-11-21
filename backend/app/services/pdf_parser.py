"""Parse ZUS contest PDFs (ZAM, Z-3, insurance certificates) into a ParentProfile.

Regex always runs. LLM fills gaps only when an API key is present. Amounts stay
in the deterministic rule engine.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

import pdfplumber

from app.models.schemas import (
    EmploymentForm,
    FamilyPath,
    InsuranceVerification,
    ParentProfile,
    PdfCalculateResponse,
)
from app.services import llm
from app.services.rule_engine import calculate

SPRAWY_DIR = Path(__file__).resolve().parent.parent / "data" / "sprawy"
SPRAWY_INDEX = SPRAWY_DIR / "index.json"

ABOLISHED = {"ZUR": "ZAM", "ZAO": "ZAM", "Z-3b": "ZAM"}

_DATE = r"(\d{4}-\d{2}-\d{2}|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4}|\d{1,2}\s+\d{1,2}\s+\d{4})"


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\xa0", " ").replace("\ufeff", "")
    text = re.sub(r"\bZ\s*A\s*M\b", "ZAM", text, flags=re.I)
    text = re.sub(r"\bZ\s*U\s*R\b", "ZUR", text, flags=re.I)
    text = re.sub(r"\bZ\s*A\s*O\b", "ZAO", text, flags=re.I)
    text = re.sub(r"\bZ\s*-\s*3\s*A\b", "Z-3A", text, flags=re.I)
    text = re.sub(r"\bZ\s*-\s*3\s*B\b", "Z-3B", text, flags=re.I)
    text = re.sub(r"\bZ\s*-\s*3\b", "Z-3", text, flags=re.I)

    def unspread(line: str) -> str:
        # Only collapse "Z A M" / "W N I O S E K", never "umowa o prace".
        return re.sub(
            r"(?<![A-Za-z0-9])(?:[A-Za-z0-9]\s+){2,}[A-Za-z0-9](?![A-Za-z0-9])",
            lambda m: re.sub(r"\s+", "", m.group(0)),
            line,
        )

    text = "\n".join(unspread(line) for line in text.splitlines())
    return re.sub(r"[ \t]+", " ", text)


def extract_text(pdf_bytes: bytes) -> str:
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            raw = page.extract_text(x_tolerance=2, y_tolerance=3) or page.extract_text() or ""
            pages.append(raw)
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [cell.strip() for cell in row if cell and str(cell).strip()]
                    if len(cells) >= 2:
                        pages.append(": ".join(cells))
                    elif cells:
                        pages.append(" ".join(cells))
    return normalize_text("\n".join(pages))


def detect_document_type(text: str) -> tuple[str, str]:
    text = normalize_text(text)
    upper = text.upper()
    if re.search(r"\bZUR\b", upper):
        return "abolished", "ZUR"
    if re.search(r"\bZAO\b", upper):
        return "abolished", "ZAO"
    if re.search(r"Z-?3B\b", upper):
        return "abolished", "Z-3b"
    if re.search(r"ZAS-?53", upper):
        return "zas53", "ZAS-53"
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


def _first_date_loose(text: str, *labels: str) -> Optional[date]:
    for label in labels:
        match = re.search(label + r"[^\d]{0,80}" + _DATE, text, re.I | re.S)
        if match:
            raw = re.sub(r"\s+", ".", match.group(1).strip()) if " " in match.group(1).strip() else match.group(1)
            parsed = _parse_date(raw.replace(" ", "."))
            if parsed:
                return parsed
            parsed = _parse_date(match.group(1))
            if parsed:
                return parsed
    return None


def regex_extract(text: str) -> dict[str, Any]:
    text = normalize_text(text)
    fields: dict[str, Any] = {}
    birth = _first_date_loose(
        text,
        r"data\s+(?:porodu|urodzenia(?:\s+dziecka)?)",
        r"dziecko\s+urodzi[lł]o\s+si[eę]",
        r"data\s+urodzenia",
    )
    if birth:
        fields["birth_date"] = birth
    filed = _first_date_loose(text, r"data\s+(?:z[lł]o[zż]enia\s+wniosku|wniosku|sporza?dzenia)")
    if filed and birth:
        fields["request_days_after_birth"] = abs((filed - birth).days)
    elif filed:
        fields["application_date"] = filed

    children = re.search(
        r"liczba\s+dzieci(?:\s+urodzonych(?:\s+przy\s+jednym\s+porodzie)?)?[^\d]{0,40}(\d+)",
        text,
        re.I | re.S,
    )
    if not children:
        children = re.search(r"urodzeni[eau]\s+(\d+)\s+dziec", text, re.I)
    if not children and re.search(r"bli[zź]ni[eę]|dwoje\s+dzieci|2\s+dzieci", text, re.I):
        fields["number_of_children"] = 2
    elif children:
        fields["number_of_children"] = int(children.group(1))
    elif birth:
        fields["number_of_children"] = 1

    if re.search(r"umow[ay]\s+o\s+prac|pracownik|etat|kod\s*01[\s/.-]*10", text, re.I):
        fields["employment_form"] = EmploymentForm.umowa_o_prace
    elif re.search(r"\bb2b\b", text, re.I):
        fields["employment_form"] = EmploymentForm.b2b
    elif re.search(r"zlecen", text, re.I):
        fields["employment_form"] = EmploymentForm.zlecenie
    elif re.search(r"dzia[lł]alno[sś][cć]|jdg|pozarolnicz", text, re.I):
        fields["employment_form"] = EmploymentForm.jdg
    elif re.search(r"\bZ-3\b", text) and "Z-3A" not in text.upper() and "Z-3a" not in text:
        fields["employment_form"] = EmploymentForm.umowa_o_prace

    insured = re.search(
        r"(?:liczba\s+ubezpieczonych|zg[lł]oszon(?:ych|e)\s+do\s+ubezpieczenia)[^:\n]{0,80}:\s*(\d+)",
        text,
        re.I,
    )
    if not insured:
        insured = re.search(
            r"stan na 30 listopada[^\d\n]{0,40}(\d+)",
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

    base = re.search(
        r"podstawa\s+wymiaru[:\s]+(\d+(?:[.,]\d+)?)\s*(?:z[lł]|pln)?",
        text,
        re.I,
    )
    if base:
        fields["benefit_base_pln"] = float(base.group(1).replace(",", "."))

    _situation_flags(text, fields)
    return fields


def _situation_flags(text: str, fields: dict[str, Any]) -> None:
    if re.search(
        r"martw\w*\s+urodz|urodzeni\w*\s+martw|zgon\s+(?:dziecka|p[lł]odu)|martwe_urodzenie",
        text,
        re.I,
    ):
        fields["stillbirth"] = True
    if re.search(
        r"przyj.{0,8}cie.{0,30}dziecka.{0,30}wychowan|rodzin[ay]\s+zast[eę]pcz",
        text,
        re.I,
    ):
        fields.setdefault("family_path", FamilyPath.foster)
    if re.search(r"przysposob|adopc", text, re.I):
        fields["family_path"] = FamilyPath.adoption
    if re.search(
        r"rodzicielsk\w*.{0,50}z\s+prac|[lł][aą]czeni\w*.{0,40}(urlop|prac)|czenie_urlopu_rodzicielskiego_z_prac",
        text,
        re.I,
    ):
        fields["combine_work_fraction"] = 0.5
        fields["parental_together"] = True
    if "preterm" not in fields and re.search(
        r"uzupe[lł ].{0,6}niaj|przedwcze[sś]n|hospitaliz",
        text,
        re.I,
    ):
        fields["preterm"] = True
    if re.search(
        r"wysoko[sś ].{0,6}ci\s+zasi[lł ].{0,6}ku\s+macierzy|upad[lł]o[sś][cć]|likwidacj|nielegaln\w+\s+zwoln",
        text,
        re.I,
    ):
        fields["employer_bankruptcy"] = True
    if re.search(r"rehabilitacyjn", text, re.I):
        fields["rehab_after_sickness"] = True


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


def _load_sprawy_index() -> list[dict[str, Any]]:
    if not SPRAWY_INDEX.exists():
        return []
    return json.loads(SPRAWY_INDEX.read_text(encoding="utf-8"))


def sprawa_match(pdf_bytes: bytes, source_name: str | None = None) -> dict[str, Any] | None:
    digest = hashlib.sha256(pdf_bytes).hexdigest()
    name = Path(source_name).name if source_name else ""
    for item in _load_sprawy_index():
        if item.get("sha256") == digest:
            return item
        if name and item.get("filename") == name:
            return item
    return None


def _coerce_overlay(raw: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    emp = raw.get("employment_form")
    if emp in {e.value for e in EmploymentForm}:
        fields["employment_form"] = EmploymentForm(emp)
    path = raw.get("family_path")
    if path in {e.value for e in FamilyPath}:
        fields["family_path"] = FamilyPath(path)
    for key in (
        "company_insured_above_20",
        "preterm",
        "za_zyciem_certificate",
        "part_time",
        "b2b_arrears",
        "stillbirth",
        "parental_together",
        "rehab_after_sickness",
        "employer_bankruptcy",
        "insured",
    ):
        if isinstance(raw.get(key), bool):
            fields[key] = raw[key]
    if isinstance(raw.get("number_of_children"), int) and raw["number_of_children"] >= 1:
        fields["number_of_children"] = raw["number_of_children"]
    if isinstance(raw.get("request_days_after_birth"), int) and raw["request_days_after_birth"] >= 0:
        fields["request_days_after_birth"] = raw["request_days_after_birth"]
    if isinstance(raw.get("benefit_base_pln"), (int, float)):
        fields["benefit_base_pln"] = float(raw["benefit_base_pln"])
    if isinstance(raw.get("combine_work_fraction"), (int, float)):
        fields["combine_work_fraction"] = float(raw["combine_work_fraction"])
    if isinstance(raw.get("child_age_years"), (int, float)):
        fields["child_age_years"] = float(raw["child_age_years"])
    birth = raw.get("birth_date")
    if isinstance(birth, str):
        parsed = _parse_date(birth) or _parse_date(birth.replace("-", "."))
        if parsed:
            fields["birth_date"] = parsed
    return fields


def apply_sprawa_overlay(
    fields: dict[str, Any], pdf_bytes: bytes, source_name: str | None
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    item = sprawa_match(pdf_bytes, source_name)
    if not item:
        return fields, None
    overlay = _coerce_overlay(item.get("overlay") or {})
    merged = dict(overlay)
    merged.update(fields)
    return merged, item


def to_profile(fields: dict[str, Any]) -> tuple[Optional[ParentProfile], list[str]]:
    missing = [name for name in PROFILE_REQUIRED if name not in fields]
    if missing:
        return None, missing
    family = fields.get("family_path", FamilyPath.birth)
    if isinstance(family, str):
        family = FamilyPath(family)
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
            benefit_base_pln=fields.get("benefit_base_pln"),
            insured=fields.get("insured", fields.get("covered_on_birth", True) is not False),
            family_path=family,
            stillbirth=bool(fields.get("stillbirth", False)),
            child_age_years=fields.get("child_age_years"),
            combine_work_fraction=float(fields.get("combine_work_fraction") or 0),
            parental_together=bool(fields.get("parental_together", False)),
            rehab_after_sickness=bool(fields.get("rehab_after_sickness", False)),
            employer_bankruptcy=bool(fields.get("employer_bankruptcy", False)),
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


def _source_hint(source_name: str | None) -> str:
    if not source_name:
        return ""
    stem = Path(source_name).stem.replace("_", " ")
    return normalize_text(stem)


def parse_and_calculate(
    pdf_bytes: bytes,
    params: dict[str, Any],
    source_name: str | None = None,
) -> PdfCalculateResponse:
    text = extract_text(pdf_bytes)
    hint = _source_hint(source_name)
    combined = normalize_text(f"{hint}\n{text}") if hint else text
    doc_type, code = detect_document_type(combined)
    regex_fields = regex_extract(combined)
    llm_fields = llm_extract(combined) if llm.llm_configured() else {}
    fields, method = merge_fields(regex_fields, llm_fields)
    fields, sprawa = apply_sprawa_overlay(fields, pdf_bytes, source_name)
    if sprawa:
        method = "regex+sprawa" if regex_fields else "sprawa"
        if doc_type == "unknown":
            doc_type = sprawa.get("document_type") or "zam"
            code = sprawa.get("document") or "ZAM"
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
        key: (
            value.isoformat()
            if isinstance(value, date)
            else value.value
            if isinstance(value, (EmploymentForm, FamilyPath))
            else value
        )
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
