"""Hybrid guided chat: one decision per step (buttons) + GraphRAG for open questions."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Optional

from app.models.schemas import (
    ChatButton,
    ChatCitation,
    ChatRequest,
    ChatResponse,
    EmploymentForm,
    ParentProfile,
)
from app.services import llm
from app.services.graph_service import GraphService
from app.services.rule_engine import calculate

YES_NO = [
    ChatButton(id="true", label="Tak"),
    ChatButton(id="false", label="Nie"),
]

STEPS: list[dict[str, Any]] = [
    {
        "id": "employment_form",
        "field": "employment_form",
        "question": "Jak pracujesz?",
        "helper": "To ustala, czy wyczekiwanie na zasiłek w ciąży to 30 czy 90 dni.",
        "buttons": [
            ChatButton(id="umowa_o_prace", label="Umowa o pracę"),
            ChatButton(id="zlecenie", label="Umowa zlecenie"),
            ChatButton(id="jdg", label="Własna firma (JDG)"),
            ChatButton(id="b2b", label="B2B"),
        ],
    },
    {
        "id": "company_size",
        "field": "company_insured_above_20",
        "skip_when_employment": {EmploymentForm.jdg, EmploymentForm.b2b},
        "skip_value": False,
        "question": "Czy Twój pracodawca zgłaszał więcej niż 20 osób do ubezpieczenia (30 listopada poprzedniego roku)?",
        "helper": "Jeśli tak, zasiłek wypłaca pracodawca. Jeśli nie — ZUS.",
        "buttons": YES_NO,
    },
    {
        "id": "children",
        "field": "number_of_children",
        "question": "Ile dzieci urodziło się przy tym porodzie?",
        "helper": "Od tego zależy długość urlopu macierzyńskiego (20 albo 31–37 tygodni).",
        "buttons": [
            ChatButton(id="1", label="Jedno"),
            ChatButton(id="2", label="Dwoje"),
            ChatButton(id="3", label="Troje"),
            ChatButton(id="4", label="Czworo"),
            ChatButton(id="5", label="Pięcioro lub więcej"),
        ],
    },
    {
        "id": "preterm",
        "field": "preterm",
        "question": "Czy dziecko urodziło się przedwcześnie albo leżało w szpitalu po porodzie?",
        "helper": "Wtedy możesz mieć uzupełniający urlop macierzyński (100%).",
        "buttons": YES_NO,
    },
    {
        "id": "za_zyciem",
        "field": "za_zyciem_certificate",
        "question": "Czy masz zaświadczenie „Za życiem”?",
        "helper": "Wydłuża urlop rodzicielski do 65 albo 67 tygodni.",
        "buttons": YES_NO,
    },
    {
        "id": "part_time",
        "field": "part_time",
        "question": "Czy pracujesz na część etatu?",
        "helper": "Urlop trwa tyle samo. Kwota zasiłku może być niższa.",
        "buttons": YES_NO,
    },
    {
        "id": "arrears",
        "field": "b2b_arrears",
        "only_when_employment": {EmploymentForm.jdg, EmploymentForm.b2b},
        "skip_value": False,
        "question": "Czy masz nieopłacone składki (zaległości)?",
        "helper": "Zaległości mogą sprawić, że ZUS nie wypłaci zasiłku.",
        "buttons": YES_NO,
    },
    {
        "id": "request_21",
        "field": "request_days_after_birth",
        "question": "Czy złożysz wniosek o zasiłek nie później niż 21 dni po porodzie?",
        "helper": "Tak = 81,5% za macierzyński i rodzicielski. Nie = 100% + 70%.",
        "buttons": [
            ChatButton(id="0", label="Tak, w ciągu 21 dni"),
            ChatButton(id="22", label="Później niż 21 dni"),
            ChatButton(id="unknown", label="Jeszcze nie wiem"),
        ],
    },
    {
        "id": "birth_date",
        "field": "birth_date",
        "question": "Jaka jest data urodzenia dziecka? Napisz np. 2026-11-01.",
        "helper": "Jedna decyzja: tylko data. Pytania o przepisy możesz zadać w każdej chwili.",
        "buttons": [],
    },
]


def _parse_date(raw: str) -> Optional[date]:
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _coerce(step: dict[str, Any], raw: str) -> Any:
    field = step["field"]
    if field == "employment_form":
        return EmploymentForm(raw)
    if field == "number_of_children":
        return int(raw)
    if field in {"company_insured_above_20", "preterm", "za_zyciem_certificate", "part_time", "b2b_arrears"}:
        return raw in {"true", "tak", "yes"}
    if field == "request_days_after_birth":
        if raw in {"unknown", "nie_wiem"}:
            return None
        return int(raw)
    if field == "birth_date":
        parsed = _parse_date(raw)
        if parsed is None:
            raise ValueError("nie_data")
        return parsed
    return raw


class ChatService:
    def __init__(self, graph: GraphService, params: dict[str, Any]) -> None:
        self.graph = graph
        self.params = params
        self.sessions: dict[str, dict[str, Any]] = {}

    def handle(self, request: ChatRequest) -> ChatResponse:
        if request.action == "start" or not request.session_id:
            session_id = uuid.uuid4().hex
            self.sessions[session_id] = {"answers": {}, "step_index": 0}
            return self._step_response(session_id)

        session_id = request.session_id
        session = self.sessions.setdefault(session_id, {"answers": {}, "step_index": 0})

        if request.action == "question" or (
            request.message
            and not request.button_id
            and self._current_step(session)
            and self._current_step(session)["field"] != "birth_date"
        ):
            return self._question_response(session_id, request.message or "")

        if self._current_step(session) and self._current_step(session)["field"] == "birth_date" and request.message:
            if _parse_date(request.message) is None and not request.button_id:
                return self._question_response(session_id, request.message)

        try:
            self._apply_answer(session, request)
        except ValueError:
            step = self._current_step(session)
            return ChatResponse(
                session_id=session_id,
                mode="step",
                question=step["question"] if step else None,
                helper="Nie rozpoznałam tej odpowiedzi. Wybierz przycisk albo podaj datę w formacie 2026-11-01.",
                buttons=step["buttons"] if step else [],
                complete=False,
            )

        self._skip_inapplicable(session)
        if self._current_step(session) is None:
            return self._result_response(session_id, session)
        return self._step_response(session_id)

    def _current_step(self, session: dict[str, Any]) -> Optional[dict[str, Any]]:
        idx = session["step_index"]
        if idx >= len(STEPS):
            return None
        return STEPS[idx]

    def _skip_inapplicable(self, session: dict[str, Any]) -> None:
        answers = session["answers"]
        while session["step_index"] < len(STEPS):
            step = STEPS[session["step_index"]]
            employment = answers.get("employment_form")
            skip_when = step.get("skip_when_employment")
            only_when = step.get("only_when_employment")
            if skip_when and employment in skip_when:
                answers[step["field"]] = step.get("skip_value")
                session["step_index"] += 1
                continue
            if only_when and employment not in only_when:
                answers[step["field"]] = step.get("skip_value")
                session["step_index"] += 1
                continue
            if step["field"] in answers:
                session["step_index"] += 1
                continue
            break

    def _apply_answer(self, session: dict[str, Any], request: ChatRequest) -> None:
        step = self._current_step(session)
        if step is None:
            return
        raw = request.button_id
        if raw is None and request.message:
            raw = self._match_button(step, request.message) or request.message.strip()
        if not raw:
            raise ValueError("empty")
        session["answers"][step["field"]] = _coerce(step, raw)
        session["step_index"] += 1

    def _match_button(self, step: dict[str, Any], message: str) -> Optional[str]:
        folded = message.strip().lower()
        for button in step["buttons"]:
            if folded in {button.id.lower(), button.label.lower()}:
                return button.id
        return None

    def _step_response(self, session_id: str) -> ChatResponse:
        session = self.sessions[session_id]
        self._skip_inapplicable(session)
        step = self._current_step(session)
        if step is None:
            return self._result_response(session_id, session)
        return ChatResponse(
            session_id=session_id,
            mode="step",
            question=step["question"],
            helper=step.get("helper"),
            buttons=step["buttons"],
            profile=self._public_answers(session),
            complete=False,
        )

    def _result_response(self, session_id: str, session: dict[str, Any]) -> ChatResponse:
        profile = self._to_profile(session["answers"])
        result = calculate(profile, self.params)
        return ChatResponse(
            session_id=session_id,
            mode="result",
            question=None,
            helper="To wynik z silnika reguł, nie z modelu językowego.",
            answer=self._result_plain(result),
            profile=profile.model_dump(mode="json"),
            calculation=result,
            complete=True,
        )

    def _question_response(self, session_id: str, message: str) -> ChatResponse:
        subgraph = self.graph.subgraph_for_query(message)
        citations = [
            ChatCitation(
                node_id=node["id"],
                title=node["title"],
                plain_language=node["plain_language"],
                legal_basis=node["legal_basis"],
            )
            for node in subgraph["nodes"]
            if node["id"] in subgraph["hit_ids"]
        ]
        if not citations:
            citations = [
                ChatCitation(
                    node_id=node["id"],
                    title=node["title"],
                    plain_language=node["plain_language"],
                    legal_basis=node["legal_basis"],
                )
                for node in subgraph["nodes"][:4]
            ]
        answer = self._phrase(message, citations)
        session = self.sessions[session_id]
        step = self._current_step(session)
        return ChatResponse(
            session_id=session_id,
            mode="question",
            question=step["question"] if step else None,
            helper=step.get("helper") if step else None,
            buttons=step["buttons"] if step else [],
            answer=answer,
            citations=citations,
            profile=self._public_answers(session),
            complete=False,
        )

    def _phrase(self, question: str, citations: list[ChatCitation]) -> str:
        facts = "\n".join(
            f"- {item.plain_language} (Podstawa prawna: {item.legal_basis})"
            for item in citations
        )
        if not facts:
            return "Nie znalazłam tego w grafie wiedzy. Wybierz przycisk albo zapytaj o urlop, wniosek ZAM, wyczekiwanie albo stawki."
        templated = (
            "Oto, co wynika z grafu wiedzy:\n"
            f"{facts}\n\n"
            "Liczby i stawki liczy silnik reguł, nie czat."
        )
        if not llm.llm_configured():
            return templated
        phrased = llm.complete(
            f"Pytanie rodzica: {question}\n\nFakty (cytuj podstawę prawną, nie wymyślaj kwot):\n{facts}",
            system=(
                "Jesteś przewodnikiem ZUS. Odpowiadasz po polsku, prosto i empatycznie. "
                "Używasz TYLKO podanych faktów. Nie licz zasiłków. "
                "Każdy akapit kończ cytatem podstawy prawnej."
            ),
        )
        return phrased or templated

    def _to_profile(self, answers: dict[str, Any]) -> ParentProfile:
        return ParentProfile(
            employment_form=answers["employment_form"],
            company_insured_above_20=bool(answers.get("company_insured_above_20", False)),
            birth_date=answers["birth_date"],
            number_of_children=int(answers["number_of_children"]),
            preterm=bool(answers.get("preterm", False)),
            za_zyciem_certificate=bool(answers.get("za_zyciem_certificate", False)),
            part_time=bool(answers.get("part_time", False)),
            b2b_arrears=bool(answers.get("b2b_arrears", False)),
            request_days_after_birth=answers.get("request_days_after_birth"),
        )

    def _public_answers(self, session: dict[str, Any]) -> dict[str, Any]:
        out = {}
        for key, value in session["answers"].items():
            if isinstance(value, date):
                out[key] = value.isoformat()
            elif isinstance(value, EmploymentForm):
                out[key] = value.value
            else:
                out[key] = value
        return out

    def _result_plain(self, result: Any) -> str:
        maternity = next(item for item in result.leaves if item.leave_type == "macierzynski")
        parental = next(item for item in result.leaves if item.leave_type == "rodzicielski")
        return (
            f"Urlop macierzyński: {maternity.weeks} tygodni, zasiłek {maternity.rate_percent:g}%. "
            f"Urlop rodzicielski: {parental.weeks} tygodni, zasiłek {parental.rate_percent:g}%. "
            f"Płatnik: {result.payer.value}. Wniosek: ZAM (nie ZUR/ZAO/Z-3b)."
        )
