"""Chat: GraphRAG internally, short plans and one follow-up at a time."""

from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Any, Optional

from app.models.schemas import ChatButton, ChatCitation, ChatRequest, ChatResponse
from app.services import llm
from app.services.graph_service import GraphService

GREETING = (
    "Cześć. Napisz, co się u Ciebie dzieje — na przykład: jestem w ciąży i uczę w szkole. "
    "Powiem, od czego zacząć. Jeśli czegoś nie będę wiedziała, zapytam o jedną rzecz."
)

TOPICS: list[ChatButton] = [
    ChatButton(id="ciaza", label="Ciąża"),
    ChatButton(id="porod", label="Urodziło się dziecko"),
    ChatButton(id="wniosek", label="Jaki wniosek"),
    ChatButton(id="zlecenie", label="Zlecenie"),
    ChatButton(id="b2b", label="B2B"),
    ChatButton(id="ojciec", label="Urlop ojcowski"),
]

TOPIC_PROMPTS: dict[str, str] = {
    "ciaza": "Jestem w ciąży i nie wiem, od czego zacząć.",
    "porod": "Urodziło się dziecko. Jaki urlop i jaki wniosek?",
    "wniosek": "Jaki wniosek złożyć po porodzie? Czy ZUR albo ZAO jeszcze obowiązują?",
    "zlecenie": "Pracuję na umowie zlecenie. Co z zasiłkiem w ciąży i po porodzie?",
    "b2b": "Prowadzę firmę / B2B. Co z zasiłkiem i składkami?",
    "ojciec": "Jestem tatą. Ile jest urlopu ojcowskiego i do kiedy?",
}

EMP_BUTTONS = [
    ChatButton(id="emp_umowa", label="Etat — umowa o pracę"),
    ChatButton(id="emp_zlecenie", label="Umowa zlecenie"),
    ChatButton(id="emp_firma", label="Własna firma / B2B"),
]

EMP_FROM_BUTTON = {
    "emp_umowa": "umowa_o_prace",
    "emp_zlecenie": "zlecenie",
    "emp_firma": "b2b",
}

DROP_FOR_UMOW = {
    "ryzyko_wyczekiwanie_90",
    "status_zlecenie",
    "status_jdg",
    "status_b2b",
    "dokument_z3a",
    "ryzyko_zaleglosci_b2b",
    "status_zaleglosci_skladek",
}
DROP_FOR_VOLUNTARY = {
    "ryzyko_wyczekiwanie_30",
    "status_umowa_o_prace",
    "dokument_z3",
}


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def _infer(message: str, prior: dict[str, Any]) -> dict[str, Any]:
    facts = dict(prior)
    folded = _fold(message)
    if any(token in folded for token in ("nauczyciel", "naucyzciel", "szkol", "etat", "umow o prac", "umowe o prac")):
        facts["employment"] = "umowa_o_prace"
    elif "zlecen" in folded:
        facts["employment"] = "zlecenie"
    elif any(token in folded for token in ("b2b", "jdg", "dzialalnosc", "firme", "wlasna firme")):
        facts["employment"] = "b2b"
    if any(token in folded for token in ("ciaz", "miesiac ciazy", "miesiacu")):
        facts["topic"] = "ciaza"
    if any(token in folded for token in ("urodz", "porod", "dzieck")) and "ojcow" not in folded:
        facts["topic"] = facts.get("topic") or "porod"
    if any(token in folded for token in ("ojcow", "tata", "jestem tatem", "jestem ojcem")):
        facts["topic"] = "ojciec"
    if any(token in folded for token in ("zur", "zao", "z-3b", "wniosek zam", "jaki wniosek")):
        facts["topic"] = facts.get("topic") or "wniosek"
    month = re.search(r"(\d+)\s*\.?\s*miesi", folded)
    if month:
        facts["pregnancy_month"] = int(month.group(1))
        facts["topic"] = facts.get("topic") or "ciaza"
    return facts


class ChatService:
    def __init__(self, graph: GraphService, params: dict[str, Any]) -> None:
        self.graph = graph
        self.params = params
        self.sessions: dict[str, dict[str, Any]] = {}

    def handle(self, request: ChatRequest) -> ChatResponse:
        if request.action == "start" or not request.session_id:
            session_id = uuid.uuid4().hex
            self.sessions[session_id] = {"facts": {}, "last": ""}
            return ChatResponse(
                session_id=session_id,
                mode="question",
                answer=GREETING,
                buttons=TOPICS,
                complete=False,
            )

        session_id = request.session_id
        session = self.sessions.setdefault(session_id, {"facts": {}, "last": ""})
        if request.button_id in EMP_FROM_BUTTON:
            session["facts"]["employment"] = EMP_FROM_BUTTON[request.button_id]
            message = session.get("last") or "Jestem w ciąży i nie wiem, od czego zacząć."
        else:
            message = self._message_from(request)
        if not message:
            return ChatResponse(
                session_id=session_id,
                mode="question",
                answer=GREETING,
                buttons=TOPICS,
                complete=False,
            )
        session["last"] = message
        session["facts"] = _infer(message, session["facts"])
        return self._reply(session_id, session, message)

    def _message_from(self, request: ChatRequest) -> str:
        if request.button_id and request.button_id in TOPIC_PROMPTS:
            return TOPIC_PROMPTS[request.button_id]
        if request.message and request.message.strip():
            return request.message.strip()
        if request.button_id:
            return request.button_id.replace("_", " ")
        return ""

    def _reply(self, session_id: str, session: dict[str, Any], message: str) -> ChatResponse:
        facts = session["facts"]
        if facts.get("topic") in {None, "ciaza"} and not facts.get("employment"):
            if facts.get("topic") == "ciaza" or "zacza" in _fold(message) or "ciaz" in _fold(message):
                if not facts.get("employment"):
                    return ChatResponse(
                        session_id=session_id,
                        mode="question",
                        answer=(
                            "Żeby powiedzieć, od czego zacząć, potrzebuję jednej informacji: "
                            "jak pracujesz? Od tego zależy, kto wypłaci zasiłek i ile wynosi wyczekiwanie."
                        ),
                        buttons=EMP_BUTTONS,
                        complete=False,
                    )

        query = self._graph_query(message, facts)
        citations = self._citations(query, facts.get("employment"))
        answer = self._compose(message, facts, citations)
        if llm.llm_configured():
            polished = llm.complete(
                f"Sytuacja: {message}\n\nSzkic odpowiedzi (nie dodawaj faktów, nie licz kwot):\n{answer}",
                system=(
                    "Jesteś spokojną doradczynią ZUS dla rodziców. Pisz po polsku, krótko, prosto. "
                    "Zostaw plan w punktach, jeśli szkic go ma. Nie wspominaj grafu, silnika ani węzłów. "
                    "Nie pytaj o liczbę dzieci. Nie wymyślaj kwot."
                ),
            )
            if polished:
                answer = polished
        buttons = self._next_buttons(facts)
        return ChatResponse(
            session_id=session_id,
            mode="question",
            answer=answer,
            buttons=buttons,
            citations=citations,
            complete=False,
        )

    def _graph_query(self, message: str, facts: dict[str, Any]) -> str:
        bits = [message]
        emp = facts.get("employment")
        if emp == "umowa_o_prace":
            bits.append("umowa o pracę etat 30 dni wyczekiwania ZAM")
        elif emp == "zlecenie":
            bits.append("zlecenie 90 dni wyczekiwania ZAM")
        elif emp in {"jdg", "b2b"}:
            bits.append("B2B JDG 90 dni wyczekiwania składki ZAM")
        topic = facts.get("topic")
        if topic == "ciaza":
            bits.append("ciąża zasiłek chorobowy kod B")
        if topic == "porod":
            bits.append("urlop macierzyński rodzicielski wniosek ZAM 21 dni")
        if topic == "ojciec":
            bits.append("urlop ojcowski 14 dni")
        if topic == "wniosek":
            bits.append("wniosek ZAM nie ZUR ZAO")
        return " ".join(bits)

    def _citations(self, query: str, employment: Optional[str]) -> list[ChatCitation]:
        subgraph = self.graph.subgraph_for_query(query)
        drop: set[str] = set()
        if employment == "umowa_o_prace":
            drop = DROP_FOR_UMOW
        elif employment in {"zlecenie", "jdg", "b2b"}:
            drop = DROP_FOR_VOLUNTARY
        citations = [
            ChatCitation(
                node_id=node["id"],
                title=node["title"],
                plain_language=node["plain_language"],
                legal_basis=node["legal_basis"],
            )
            for node in subgraph["nodes"]
            if node["id"] in subgraph["hit_ids"] and node["id"] not in drop
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
                if node["id"] not in drop
            ]
        return citations

    def _compose(self, message: str, facts: dict[str, Any], citations: list[ChatCitation]) -> str:
        folded = _fold(message)
        if any(token in folded for token in ("zur", "zao", "z-3b")):
            return (
                "ZUR, ZAO i Z-3b już nie składaj — od 24 października 2026 jest jeden wniosek: ZAM. "
                "To ten sam wniosek o zasiłek macierzyński i rodzicielski."
            )
        topic = facts.get("topic")
        emp = facts.get("employment")
        if topic == "ojciec":
            return (
                "Urlop ojcowski to 14 dni (2 tygodnie) do ukończenia przez dziecko 12 miesięcy. "
                "Zasiłek 100%. Składasz wniosek ZAM — nie stare ZUR.\n\n"
                "Chcesz, żebym dopisała, jak to zestawić z urlopem mamy?"
            )
        if topic == "wniosek" and topic != "porod":
            return (
                "Po porodzie składasz wniosek ZAM (jeden druk). Starych ZUR, ZAO i Z-3b nie ma. "
                "Jeśli złożysz ZAM w ciągu 21 dni od porodu, wychodzi 81,5% za macierzyński i rodzicielski razem. "
                "Później: 100% za macierzyński i 70% za rodzicielski."
            )
        if topic == "ciaza" or (emp and "zacza" in folded):
            return self._plan_pregnancy(facts)
        if topic == "porod":
            return self._plan_birth(facts)
        if citations:
            first = citations[0].plain_language
            return f"{first}\n\nJeśli chcesz, opisz krótko jak pracujesz — ułożę z tego konkretny plan krok po kroku."
        return (
            "Nie jestem pewna, o co pytasz. Napisz, czy jesteś w ciąży, po porodzie, czy chcesz urlop taty — "
            "albo wybierz temat poniżej."
        )

    def _plan_pregnancy(self, facts: dict[str, Any]) -> str:
        month = facts.get("pregnancy_month")
        emp = facts.get("employment")
        when = f"w {month}. miesiącu ciąży" if month else "w ciąży"
        if emp == "umowa_o_prace":
            return (
                f"Jesteś {when} i pracujesz na etacie. Oto prosty plan — od teraz do urlopu.\n\n"
                "1. Teraz\n"
                "Jeśli lekarz da L4 w ciąży (kod B), zasiłek chorobowy to 100% podstawy. "
                "Na umowie o pracę wyczekiwanie wynosi 30 dni — w szkole zwykle już je masz. "
                "L4 idzie elektronicznie do pracodawcy.\n\n"
                "2. Kto płaci\n"
                "Szkoła z więcej niż 20 ubezpieczonymi sama wypłaca zasiłek. "
                "Mniejsza szkoła przekazuje do ZUS zaświadczenie Z-3.\n\n"
                "3. Po porodzie (ważne: 21 dni)\n"
                "Składasz jeden wniosek ZAM. ZUR, ZAO i Z-3b są zniesione. "
                "ZAM w ciągu 21 dni od porodu = 81,5% za macierzyński i rodzicielski. "
                "Później = 100% macierzyński i 70% rodzicielski.\n\n"
                "4. Urlopy (przy jednym dziecku)\n"
                "Macierzyński 20 tygodni (pierwsze 14 tylko dla Ciebie), potem rodzicielski 41 tygodni "
                "(9 tygodni nieoddawalne dla każdego rodzica).\n\n"
                "Napisz, czy rozwinąć L4 w ciąży, wniosek ZAM, albo urlop taty."
            )
        if emp in {"zlecenie", "b2b", "jdg"}:
            wait = "90 dni dobrowolnego ubezpieczenia chorobowego"
            who = "ZUS (zleceniodawca daje Z-3a)" if emp == "zlecenie" else "ZUS — dopilnuj opłaconych składek"
            return (
                f"Jesteś {when} i pracujesz na {('zleceniu' if emp == 'zlecenie' else 'własnej działalności')}. "
                "Plan:\n\n"
                f"1. Teraz — L4 w ciąży (kod B) to 100%, ale najpierw {wait}. {who}.\n"
                "2. Po porodzie — wniosek ZAM, nie ZUR/ZAO. 21 dni od porodu decyduje o 81,5% albo 100%+70%.\n"
                "3. Urlop przy jednym dziecku — 20 tygodni macierzyńskiego, potem 41 rodzicielskiego.\n\n"
                "Masz opłacone chorobowe? Jeśli nie, to pierwszy krok."
            )
        return (
            f"Jesteś {when}. Żeby ułożyć plan, powiedz jeszcze, jak pracujesz: etat, zlecenie czy firma."
        )

    def _plan_birth(self, facts: dict[str, Any]) -> str:
        emp = facts.get("employment")
        payer = ""
        if emp == "umowa_o_prace":
            payer = " Pracodawca wypłaca, jeśli zgłasza powyżej 20 osób; inaczej ZUS (Z-3)."
        return (
            "Po porodzie, po kolei:\n\n"
            "1. Wniosek ZAM — jeden druk zamiast ZUR, ZAO i Z-3b.\n"
            "2. Do 21 dni od porodu — jeśli chcesz 81,5% za macierzyński i rodzicielski razem.\n"
            "3. Urlop (jedno dziecko) — 20 tygodni macierzyńskiego (14 tylko dla mamy), "
            "potem 41 tygodni rodzicielskiego.\n"
            f"4. Płatnik.{payer or ' ZUS albo pracodawca — zależy od liczby ubezpieczonych.'}\n\n"
            "Tata ma osobno 14 dni urlopu ojcowskiego do 12. miesiąca życia dziecka."
        )

    def _next_buttons(self, facts: dict[str, Any]) -> list[ChatButton]:
        if facts.get("topic") == "ciaza":
            return [
                ChatButton(id="ciaza", label="L4 w ciąży"),
                ChatButton(id="wniosek", label="Wniosek ZAM"),
                ChatButton(id="ojciec", label="Urlop taty"),
            ]
        if facts.get("topic") == "porod":
            return [
                ChatButton(id="wniosek", label="Wniosek ZAM"),
                ChatButton(id="ojciec", label="Urlop taty"),
            ]
        return TOPICS
