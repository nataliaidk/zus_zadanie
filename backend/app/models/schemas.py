from datetime import date
from enum import Enum
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class EmploymentForm(str, Enum):
    umowa_o_prace = "umowa_o_prace"
    zlecenie = "zlecenie"
    jdg = "jdg"
    b2b = "b2b"


class FamilyPath(str, Enum):
    birth = "birth"
    adoption = "adoption"
    foster = "foster"


class Payer(str, Enum):
    employer = "pracodawca"
    zus = "ZUS"


class ParentProfile(BaseModel):
    employment_form: EmploymentForm
    company_insured_above_20: bool = Field(
        description="Płatnik zgłaszał powyżej 20 ubezpieczonych na 30 listopada poprzedniego roku."
    )
    birth_date: date
    number_of_children: int = Field(ge=1, le=20)
    preterm: bool = False
    za_zyciem_certificate: bool = False
    part_time: bool = False
    b2b_arrears: bool = False
    request_days_after_birth: Optional[int] = Field(
        default=None,
        ge=0,
        description="Ile dni po porodzie matka złożyła wniosek o zasiłek macierzyński. Brak = nie wiadomo.",
    )
    transfer_first_14_weeks_to_other_parent: bool = False
    family_path: FamilyPath = FamilyPath.birth
    insured: bool = True
    insurance_days: Optional[int] = Field(default=None, ge=0)
    stillbirth: bool = False
    child_age_years: Optional[float] = Field(default=None, ge=0)
    school_deferred: bool = False
    employer_bankruptcy: bool = False
    unlawful_dismissal: bool = False
    job_ended_before_birth: bool = False
    apparent_contract: bool = False
    benefit_base_pln: Optional[float] = Field(default=None, ge=0)
    combine_work_fraction: float = Field(default=0, ge=0, le=0.5)
    parental_together: bool = False
    rehab_after_sickness: bool = False
    mother_hospitalized: bool = False
    mother_incapacity: bool = False


class LeaveItem(BaseModel):
    leave_type: str
    title: str
    weeks: Optional[int] = None
    days: Optional[int] = None
    rate_percent: float
    transferable: bool
    mother_only: bool = False
    graph_node_id: str
    plain_language: str
    amount_pln: Optional[float] = None
    calendar_weeks: Optional[float] = None


class DocumentItem(BaseModel):
    code: str
    title: str
    active: bool
    replaced_by: Optional[str] = None
    plain_language: str
    graph_node_id: str


class RiskItem(BaseModel):
    code: str
    title: str
    severity: str
    plain_language: str
    graph_node_id: str


class PregnancyItem(BaseModel):
    code: str
    title: str
    entitled: bool
    rate_percent: Optional[float] = None
    max_days: Optional[int] = None
    amount_pln: Optional[float] = None
    plain_language: str


class FilingItem(BaseModel):
    where: str
    what: str
    deadline: str
    plain_language: str


class CalculationResult(BaseModel):
    legal_as_of: str
    waiting_period_days: int
    payer: Payer
    combined_rate_applied: bool
    leaves: list[LeaveItem]
    documents: list[DocumentItem]
    risks: list[RiskItem]
    blocked: bool = False
    block_reason: Optional[str] = None
    explanation_node_ids: list[str]
    poka_yoke: list[str]
    pregnancy: list[PregnancyItem] = Field(default_factory=list)
    filing: list[FilingItem] = Field(default_factory=list)
    monthly_base_pln: Optional[float] = None
    family_path: str = "birth"


class ExplainRequest(BaseModel):
    node_id: str
    target_id: Optional[str] = None
    depth: int = Field(default=2, ge=1, le=6)


class GraphNodeOut(BaseModel):
    id: str
    type: str
    title: str
    plain_language: str
    legal_basis: str


class GraphEdgeOut(BaseModel):
    source: str
    target: str
    relation: str
    plain_language: str = ""


class ExplainResponse(BaseModel):
    question: str = "Skąd ten wynik?"
    node_id: str
    target_id: Optional[str] = None
    narrative: list[str]
    path: list[str]
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


class AdminParams(BaseModel):
    """Loose wrapper so PUT can replace the params file after key checks."""

    model_config = {"extra": "allow"}

    legal_as_of: str
    waiting_period_days: dict[str, int]
    maternity_weeks_by_children: dict[str, int]
    rates_percent: dict[str, float]
    combined_rate_request_deadline_days: int
    employer_pays_if_insured_above: int
    forms: dict[str, Any]
    non_transferable_weeks_per_parent: int
    mother_only_weeks: int
    parental_weeks: dict[str, int]

    @field_validator("waiting_period_days")
    @classmethod
    def waiting_keys(cls, value: dict[str, int]) -> dict[str, int]:
        required = {"umowa_o_prace", "zlecenie", "jdg", "b2b"}
        missing = required - set(value)
        if missing:
            raise ValueError(f"Brakuje okresów wyczekiwania: {sorted(missing)}")
        return value


class InsuranceVerification(BaseModel):
    covered_on_birth: Optional[bool] = None
    waiting_period_days: Optional[int] = None
    waiting_period_met: Optional[bool] = None
    insurance_start: Optional[date] = None
    payer_hint: Optional[str] = None
    arrears: Optional[bool] = None
    notes: list[str] = Field(default_factory=list)
    graph_node_ids: list[str] = Field(default_factory=list)


class PdfCalculateResponse(BaseModel):
    document_type: str
    document_code: str
    extraction_method: str
    profile: Optional[ParentProfile] = None
    missing_fields: list[str] = Field(default_factory=list)
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    insurance: InsuranceVerification
    calculation: Optional[CalculationResult] = None
    abolished_form_warning: Optional[str] = None
    plain_language: str


class ChatButton(BaseModel):
    id: str
    label: str


class ChatCitation(BaseModel):
    node_id: str
    title: str
    plain_language: str
    legal_basis: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    action: Literal["start", "answer", "question"] = "start"
    button_id: Optional[str] = None
    message: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    mode: Literal["step", "question", "result"]
    question: Optional[str] = None
    helper: Optional[str] = None
    buttons: list[ChatButton] = Field(default_factory=list)
    answer: Optional[str] = None
    citations: list[ChatCitation] = Field(default_factory=list)
    profile: Optional[dict[str, Any]] = None
    calculation: Optional[CalculationResult] = None
    complete: bool = False
