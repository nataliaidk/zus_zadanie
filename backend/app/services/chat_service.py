"""Chat: GraphRAG internally, context + short answers, refuse off-limits asks."""

from __future__ import annotations

import re
import unicodedata
import uuid
from typing import Any, Optional

from app.models.schemas import ChatButton, ChatCitation, ChatRequest, ChatResponse
from app.services import llm
from app.services.graph_service import GraphService

GREETING = (
    "Cześć. Jestem Przewodnikiem — powiedz, co się u Ciebie dzieje, zwyczajnym zdaniem. "
    "Na przykład: jestem w siódmym miesiącu i uczę w szkole. "
    "Odpowiem krótko. Jeśli czegoś brakuje, zapytam o jedną rzecz."
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
    "ciaza": "Co z L4 w ciąży?",
    "porod": "Urodziło się dziecko. Jaki urlop i jaki wniosek?",
    "wniosek": "Kiedy i jaki wniosek złożyć po porodzie?",
    "zlecenie": "Pracuję na umowie zlecenie. Co z zasiłkiem w ciąży i po porodzie?",
    "b2b": "Prowadzę firmę / B2B. Co z zasiłkiem i składkami?",
    "ojciec": "Jak wygląda urlop ojcowski?",
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

REFUSE = (
    "Tego nie zrobię. To przewodnik — nic nie wysyłam do ZUS, nie loguję Cię na PUE "
    "i nie wystawiam dokumentów. Mogę powiedzieć, jaki wniosek złożysz sama "
    "u pracodawcy albo na PUE/eZUS."
)

REFUSE_MARKERS = (
    "zignoruj instruk",
    "ignore previous",
    "ignore all",
    "jailbreak",
    "developer mode",
    "system prompt",
    "wyslij do zus",
    "wyslij wniosek",
    "zloz za mnie",
    "zloz wniosek za",
    "zaloguj mnie do",
    "zaloguj mnie na pue",
    "prawdziwy zus",
    "haslo pue",
    "haslo do zus",
    "wygeneruj l4",
    "wystaw l4",
    "falszyw",
    "fałszyw",
    "oszukac zus",
    "obejsc zus",
    "fikcyjn",
    "lewa umowa",
    "api key",
    "pesel kogo",
)


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn").lower()


def _unauthorized(message: str) -> bool:
    folded = _fold(message)
    return any(marker in folded for marker in REFUSE_MARKERS)


def _infer(message: str, prior: dict[str, Any]) -> dict[str, Any]:
    facts = dict(prior)
    folded = _fold(message)
    if any(
        token in folded
        for token in ("nauczyciel", "naucyzciel", "szkol", "etat", "umow o prac", "umowe o prac")
    ):
        facts["employment"] = "umowa_o_prace"
    elif "zlecen" in folded:
        facts["employment"] = "zlecenie"
    elif any(token in folded for token in ("b2b", "jdg", "dzialalnosc", "firme", "wlasna firme")):
        facts["employment"] = "b2b"
    if any(token in folded for token in ("ciaz", "miesiac ciazy", "miesiacu")):
        facts["topic"] = "ciaza"
    elif (
        any(token in folded for token in ("urodz", "porod"))
        and "ojcow" not in folded
        and facts.get("topic") != "ciaza"
    ):
        facts["topic"] = "porod"
    if any(token in folded for token in ("ojcow", "tata", "jestem tatem", "jestem ojcem")):
        facts["focus"] = "ojciec"
    if any(token in folded for token in ("zur", "zao", "z-3b", "wniosek", " zam")):
        facts["focus"] = "zam"
    if any(token in folded for token in ("l4", "e-zla", "ezla", "zwolnien", "kod b", "chorob")):
        facts["focus"] = "l4"
    if any(token in folded for token in ("kto placi", "platnik", "kto wyplac")):
        facts["focus"] = "payer"
    if any(token in folded for token in ("81", "70%", "70 %", "stawk", "ile procent")):
        facts["focus"] = "rate"
    if any(token in folded for token in ("ile trwa", "ile tygod", "wymiar", "macierzyn", "rodzicielsk")):
        facts["focus"] = facts.get("focus") or "duration"
    month = re.search(r"(\d+)\s*\.?\s*miesi", folded)
    if month:
        facts["pregnancy_month"] = int(month.group(1))
        facts["topic"] = facts.get("topic") or "ciaza"
    return facts


def _wants_plan(folded: str, facts: dict[str, Any]) -> bool:
    if facts.get("focus"):
        return False
    return any(
        token in folded
        for token in ("od czego", "zacza", "co robic", "co zrobic", "nie wiem", "porad")
    ) or (facts.get("topic") == "ciaza" and not facts.get("asked"))


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

        if _unauthorized(message):
            return ChatResponse(
                session_id=session_id,
                mode="question",
                answer=REFUSE,
                buttons=TOPICS,
                complete=False,
            )

        session["facts"]["focus"] = None
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
        folded = _fold(message)
        needs_job = not facts.get("employment") and (
            facts.get("topic") == "ciaza" or "ciaz" in folded or "zacza" in folded
        )
        if needs_job and not facts.get("focus"):
            return ChatResponse(
                session_id=session_id,
                mode="question",
                answer=(
                    "Żeby powiedzieć, od czego zacząć, potrzebuję jednej informacji: "
                    "jak pracujesz?"
                ),
                buttons=EMP_BUTTONS,
                complete=False,
            )

        query = self._graph_query(message, facts)
        citations = self._citations(query, facts.get("employment"))
        answer = self._compose(message, facts, citations)
        facts["asked"] = True
        if llm.llm_configured():
            polished = llm.complete(
                f"Sytuacja (kontekst): {facts}\nPytanie: {message}\n\nSzkic:\n{answer}",
                system=(
                    "Doradczyni zasiłkowa. Polski, ciepło, krótko. Jedno pytanie na raz. "
                    "Plan najwyżej 4 krótkie punkty. Nie cytuj ustaw. Nie wspominaj grafu. "
                    "Nie pytaj o liczbę dzieci. Nie licz złotówek. "
                    "Odmawiaj wysyłki wniosków, logowania do ZUS i fałszywych dokumentów."
                ),
            )
            if polished:
                answer = polished
        return ChatResponse(
            session_id=session_id,
            mode="question",
            answer=answer,
            buttons=self._next_buttons(facts),
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
        focus = facts.get("focus") or facts.get("topic")
        if focus == "l4" or facts.get("topic") == "ciaza":
            bits.append("ciąża zasiłek chorobowy kod B")
        if focus in {"zam", "wniosek"} or facts.get("topic") == "porod":
            bits.append("wniosek ZAM 21 dni nie ZUR")
        if focus == "ojciec":
            bits.append("urlop ojcowski 14 dni")
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
        focus = facts.get("focus")
        if focus == "zam" or any(token in folded for token in ("zur", "zao", "z-3b", "zam")):
            return (
                "Składasz jeden wniosek ZAM — u pracodawcy albo na PUE. "
                "Stare ZUR, ZAO i Z-3b już nie składaj. "
                "Jeśli ZAM wpłynie w 21 dni od porodu, masz 81,5% za macierzyński i rodzicielski. "
                "Później: 100% za macierzyński i 70% za rodzicielski."
            )
        if focus == "l4":
            wait = (
                "Na etacie potrzeba 30 dni ubezpieczenia — w szkole zwykle już je masz."
                if facts.get("employment") == "umowa_o_prace"
                else "Na zleceniu albo na firmie trzeba 90 dni opłaconego chorobowego."
                if facts.get("employment") in {"zlecenie", "b2b", "jdg"}
                else "Na etacie 30 dni ubezpieczenia, na zleceniu albo firmie 90."
            )
            return (
                f"L4 w ciąży to 100% podstawy, maksymalnie 270 dni. {wait} "
                "Lekarz wystawia e-ZLA (kod B) — Ty nic nie nosisz do ZUS. "
                "Chcesz potem usłyszeć o wniosku ZAM?"
            )
        if focus == "payer":
            if facts.get("employment") == "umowa_o_prace":
                return (
                    "Przy etacie: jeśli pracodawca zgłaszał powyżej 20 ubezpieczonych "
                    "(stan na 30 listopada poprzedniego roku), sam wypłaca zasiłek. "
                    "Mniejszy pracodawca przekazuje Z-3 do ZUS i zasiłek płaci ZUS."
                )
            if facts.get("employment") == "zlecenie":
                return "Na zleceniu zasiłek zwykle płaci ZUS. Zleceniodawca składa Z-3a."
            if facts.get("employment") in {"b2b", "jdg"}:
                return "Na B2B/JDG zasiłek płaci ZUS. Musisz mieć opłacone chorobowe — zaległości mogą zablokować wypłatę."
            return "Powiedz, czy jesteś na etacie, zleceniu czy na firmie — wtedy powiem, kto płaci."
        if focus == "ojciec":
            return (
                "Urlop ojcowski: 14 dni kalendarzowych do ukończenia przez dziecko 12 miesięcy, zasiłek 100%. "
                "Wniosek ZAM, nie ZUR. To osobno od 9 tygodni rodzicielskiego, których tata nie może oddać mamie."
            )
        if focus == "rate":
            return (
                "Dwie ścieżki: ZAM do 21 dni po porodzie = 81,5% za macierzyński i rodzicielski. "
                "Później = 100% macierzyński (i ojcowski) oraz 70% rodzicielski. Kwot nie zgaduję — do złotówek jest kalkulator."
            )
        if focus == "duration":
            return (
                "Przy jednym dziecku: 20 tygodni macierzyńskiego (pierwsze 14 tylko dla mamy), "
                "potem 41 tygodni rodzicielskiego. Tata ma osobno 14 dni ojcowskiego. "
                "Jeśli będzie więcej dzieci albo zaświadczenie „Za życiem” — daj znać, przeliczę wymiar."
            )
        if _wants_plan(folded, facts) and facts.get("employment"):
            if facts.get("topic") == "porod":
                return self._plan_birth(facts)
            return self._plan_pregnancy(facts)
        if facts.get("topic") == "porod" and _wants_plan(folded, facts):
            return self._plan_birth(facts)
        if facts.get("asked"):
            return (
                "Pamiętam, co już powiedziałaś. Napisz jedną rzecz: L4, wniosek ZAM, "
                "kto wypłaci zasiłek, albo urlop taty."
            )
        if citations:
            return citations[0].plain_language + " Mogę dopytać o L4, ZAM albo kto płaci — wybierz jedno."
        return "Napisz, czy jesteś w ciąży, po porodzie, czy pytasz o urlop taty — albo wybierz temat poniżej."

    def _plan_pregnancy(self, facts: dict[str, Any]) -> str:
        month = facts.get("pregnancy_month")
        emp = facts.get("employment")
        when = f"w {month}. miesiącu ciąży" if month else "w ciąży"
        if emp == "umowa_o_prace":
            return (
                f"Jesteś {when} i pracujesz na etacie. Krótki plan:\n\n"
                "1. Teraz — L4 w ciąży to 100% po 30 dniach ubezpieczenia; w szkole zwykle już je masz.\n"
                "2. Po porodzie złóż ZAM w 21 dni (nie ZUR). Wtedy 81,5% za macierzyński i rodzicielski.\n"
                "3. Przy jednym dziecku: 20 tygodni macierzyńskiego, potem 41 rodzicielskiego.\n\n"
                "Chcesz najpierw o L4?"
            )
        if emp in {"zlecenie", "b2b", "jdg"}:
            wait = "90 dni dobrowolnego chorobowego"
            who = "ZUS (Z-3a)" if emp == "zlecenie" else "ZUS — bez zaległości składek"
            return (
                f"Jesteś {when} na {('zleceniu' if emp == 'zlecenie' else 'działalności')}. Plan:\n\n"
                f"1. Teraz — L4 kod B, 100%, po {wait}. Płaci {who}.\n"
                "2. Po porodzie — ZAM, nie ZUR. 21 dni decyduje o 81,5% albo 100%+70%.\n"
                "3. Jedno dziecko — 20 tyg. macierzyńskiego, 41 rodzicielskiego."
            )
        return f"Jesteś {when}. Powiedz, jak pracujesz: etat, zlecenie czy firma."

    def _plan_birth(self, facts: dict[str, Any]) -> str:
        extra = ""
        if facts.get("employment") == "umowa_o_prace":
            extra = " Przy etacie duży pracodawca płaci sam, mniejszy — ZUS po Z-3."
        return (
            "Po porodzie:\n"
            "1. ZAM — jeden wniosek, bez ZUR/ZAO/Z-3b.\n"
            "2. Do 21 dni, jeśli chcesz 81,5% za macierzyński i rodzicielski.\n"
            "3. Jedno dziecko — 20 tyg. macierzyńskiego, 41 rodzicielskiego.\n"
            f"4. Tata — 14 dni ojcowskiego do 12. miesiąca.{extra}"
        )

    def _next_buttons(self, facts: dict[str, Any]) -> list[ChatButton]:
        if facts.get("topic") in {"ciaza", "porod"} or facts.get("employment"):
            return [
                ChatButton(id="ciaza", label="L4 w ciąży"),
                ChatButton(id="wniosek", label="Wniosek ZAM"),
                ChatButton(id="ojciec", label="Urlop taty"),
            ]
        return TOPICS
