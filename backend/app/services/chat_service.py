"""Guided chat: GraphRAG for answers, no wizard, no graph jargon in user text."""

from __future__ import annotations

import uuid
from typing import Any

from app.models.schemas import ChatButton, ChatCitation, ChatRequest, ChatResponse
from app.services import llm
from app.services.graph_service import GraphService

GREETING = (
    "Dzień dobry. Pomogę Ci ogarnąć urlopy i zasiłki — spokojnie, po kolei. "
    "Opisz, co się u Ciebie dzieje: na przykład że jesteś w ciąży i pracujesz na etacie, "
    "że urodziło się dziecko i nie wiesz, jaki wniosek złożyć, albo że partner chce urlop ojcowski. "
    "Podpowiem, co zrobić."
)

TOPICS: list[ChatButton] = [
    ChatButton(id="ciaza", label="Jestem w ciąży"),
    ChatButton(id="porod", label="Urodziło się dziecko"),
    ChatButton(id="wniosek", label="Jaki wniosek złożyć?"),
    ChatButton(id="zlecenie", label="Pracuję na zleceniu"),
    ChatButton(id="b2b", label="Prowadzę firmę / B2B"),
    ChatButton(id="ojciec", label="Urlop ojcowski"),
]

TOPIC_PROMPTS: dict[str, str] = {
    "ciaza": "Jestem w ciąży. Co powinnam teraz zrobić z zasiłkiem chorobowym i dokumentami?",
    "porod": "Urodziło się dziecko. Jaki urlop mi przysługuje i jaki wniosek złożyć?",
    "wniosek": "Jaki wniosek złożyć po porodzie? Czy ZUR albo ZAO jeszcze obowiązują?",
    "zlecenie": "Pracuję na umowie zlecenie. Jak wygląda zasiłek macierzyński i wyczekiwanie?",
    "b2b": "Prowadzę działalność albo B2B. Co z zasiłkiem i składkami?",
    "ojciec": "Jestem tatą. Ile wynosi urlop ojcowski i do kiedy mogę go wziąć?",
}

NO_HIT = (
    "Nie mam pewnej odpowiedzi na to pytanie. Mogę pomóc przy urlopie macierzyńskim, "
    "rodzicielskim, ojcowskim, wniosku ZAM albo zasiłku w ciąży. Opisz swoją sytuację "
    "albo wybierz jeden z tematów poniżej."
)


class ChatService:
    def __init__(self, graph: GraphService, params: dict[str, Any]) -> None:
        self.graph = graph
        self.params = params
        self.sessions: dict[str, dict[str, Any]] = {}

    def handle(self, request: ChatRequest) -> ChatResponse:
        if request.action == "start" or not request.session_id:
            session_id = uuid.uuid4().hex
            self.sessions[session_id] = {"turns": 0}
            return ChatResponse(
                session_id=session_id,
                mode="question",
                answer=GREETING,
                buttons=TOPICS,
                complete=False,
            )

        session_id = request.session_id
        self.sessions.setdefault(session_id, {"turns": 0})
        message = self._message_from(request)
        if not message:
            return ChatResponse(
                session_id=session_id,
                mode="question",
                answer=GREETING,
                buttons=TOPICS,
                complete=False,
            )
        self.sessions[session_id]["turns"] += 1
        return self._question_response(session_id, message)

    def _message_from(self, request: ChatRequest) -> str:
        if request.button_id and request.button_id in TOPIC_PROMPTS:
            return TOPIC_PROMPTS[request.button_id]
        if request.message and request.message.strip():
            return request.message.strip()
        if request.button_id:
            return request.button_id.replace("_", " ")
        return ""

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
        return ChatResponse(
            session_id=session_id,
            mode="question",
            answer=self._phrase(message, citations),
            buttons=TOPICS,
            citations=citations,
            complete=False,
        )

    def _phrase(self, question: str, citations: list[ChatCitation]) -> str:
        facts = "\n".join(
            f"- {item.plain_language} (Podstawa prawna: {item.legal_basis})"
            for item in citations
        )
        if not facts:
            return NO_HIT
        templated = (
            "Oto, co wynika z przepisów (stan na listopad 2026):\n"
            f"{facts}\n\n"
            "Kwoty zasiłku policzysz w kalkulatorze — tu podpowiadam, co zrobić i jaki wniosek złożyć."
        )
        if not llm.llm_configured():
            return templated
        phrased = llm.complete(
            f"Pytanie rodzica: {question}\n\nFakty (cytuj podstawę prawną, nie wymyślaj kwot):\n{facts}",
            system=(
                "Jesteś doradcą na stronie dla przyszłych rodziców. Odpowiadasz po polsku, "
                "krótko, ciepło i konkretnie: co zrobić teraz, jaki wniosek (ZAM), czego nie składać. "
                "Nigdy nie wspominaj o grafie wiedzy, GraphRAG, węzłach ani silniku reguł. "
                "Używasz TYLKO podanych faktów. Nie licz zasiłków."
            ),
        )
        return phrased or templated
