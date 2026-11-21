from app.models.schemas import ChatRequest
from app.services.chat_service import GREETING, ChatService
from app.services.graph_service import GraphService


def _no_graph_jargon(text: str | None) -> None:
    blob = (text or "").lower()
    assert "graf" not in blob
    assert "graphrag" not in blob
    assert "węzeł" not in blob
    assert "wezel" not in blob


def test_chat_starts_with_guidance_not_children_quiz(params):
    chat = ChatService(GraphService(), params)
    start = chat.handle(ChatRequest(action="start"))
    blob = f"{start.question or ''} {start.helper or ''} {start.answer or ''}".lower()
    assert [item.id for item in start.buttons] == [
        "ciaza",
        "porod",
        "wniosek",
        "zlecenie",
        "b2b",
        "ojciec",
    ]
    assert start.answer
    assert "ile dzieci" not in blob
    assert GREETING[:20] in (start.answer or "")
    _no_graph_jargon(start.answer)

    response = chat.handle(
        ChatRequest(
            session_id=start.session_id,
            action="question",
            message="Jaki wniosek ZAM złożyć po urodzeniu dziecka?",
        )
    )
    assert response.mode == "question"
    assert response.citations
    assert any("ZAM" in item.plain_language or "ZAM" in item.title for item in response.citations)
    _no_graph_jargon(response.answer)


def test_open_question_uses_graph_quietly(params):
    chat = ChatService(GraphService(), params)
    start = chat.handle(ChatRequest(action="start"))
    response = chat.handle(
        ChatRequest(
            session_id=start.session_id,
            action="question",
            message="Czy moge jeszcze zlozyc ZUR albo ZAO?",
        )
    )
    assert response.mode == "question"
    assert response.complete is False
    assert response.citations
    assert any("ZAM" in item.plain_language or "ZAM" in item.title for item in response.citations)
    assert all(item.legal_basis for item in response.citations)
    assert "ZAM" in (response.answer or "")
    _no_graph_jargon(response.answer)


def test_teacher_pregnancy_gets_etat_plan_not_zlecenie_wait(params):
    chat = ChatService(GraphService(), params)
    start = chat.handle(ChatRequest(action="start"))
    response = chat.handle(
        ChatRequest(
            session_id=start.session_id,
            action="question",
            message="jestem w 7 miesiacu ciazy; pracuej jako naucyzcielka w szkole i nie wiem od czego zacząć",
        )
    )
    answer = response.answer or ""
    assert "90 dni" not in answer
    assert "30 dni" in answer
    assert "ZAM" in answer
    assert "1." in answer and "2." in answer
    assert not any(item.node_id == "ryzyko_wyczekiwanie_90" for item in response.citations)
    _no_graph_jargon(answer)


def test_pregnancy_without_job_asks_one_question(params):
    chat = ChatService(GraphService(), params)
    start = chat.handle(ChatRequest(action="start"))
    response = chat.handle(
        ChatRequest(
            session_id=start.session_id,
            action="question",
            message="Jestem w ciąży i nie wiem od czego zacząć",
        )
    )
    assert "jak pracujesz" in (response.answer or "").lower()
    assert [item.id for item in response.buttons] == ["emp_umowa", "emp_zlecenie", "emp_firma"]
    follow = chat.handle(
        ChatRequest(session_id=start.session_id, action="answer", button_id="emp_umowa")
    )
    assert "30 dni" in (follow.answer or "")
    assert "90 dni" not in (follow.answer or "")


def test_topic_button_hits_graph(params):
    chat = ChatService(GraphService(), params)
    start = chat.handle(ChatRequest(action="start"))
    response = chat.handle(
        ChatRequest(session_id=start.session_id, action="answer", button_id="wniosek")
    )
    assert response.citations
    _no_graph_jargon(response.answer)


def test_graph_search_finds_waiting_period():
    hits = GraphService().search("ile dni wyczekiwania na umowie zlecenie")
    assert "ryzyko_wyczekiwanie_90" in hits or "przepis_wyczekiwanie" in hits
