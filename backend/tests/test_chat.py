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
    assert start.mode == "question"
    assert start.buttons
    assert start.answer
    assert "dzieci" not in (start.question or "").lower()
    assert "Ile dzieci" not in (start.answer or "")
    assert GREETING[:20] in (start.answer or "")
    _no_graph_jargon(start.answer)


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
    assert "Podstawa prawna" in (response.answer or "") or any(
        item.legal_basis in (response.answer or "") for item in response.citations
    )
    _no_graph_jargon(response.answer)


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
