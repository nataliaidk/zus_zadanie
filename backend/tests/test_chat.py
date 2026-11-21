from app.models.schemas import ChatRequest
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService


def test_chat_buttons_then_calculate(params):
    chat = ChatService(GraphService(), params)
    start = chat.handle(ChatRequest(action="start"))
    assert start.mode == "step"
    assert start.buttons
    session = start.session_id

    def answer(button_id=None, message=None):
        return chat.handle(
            ChatRequest(session_id=session, action="answer", button_id=button_id, message=message)
        )

    assert answer(button_id="umowa_o_prace").question
    assert answer(button_id="false").question  # small payer
    assert answer(button_id="1").question
    assert answer(button_id="false").question  # preterm
    assert answer(button_id="false").question  # za zyciem
    assert answer(button_id="false").question  # part time
    # arrears skipped for umowa
    mid = answer(button_id="0")  # 21 days
    assert mid.mode == "step"
    result = answer(message="2026-11-01")
    assert result.complete is True
    assert result.calculation is not None
    assert result.calculation.waiting_period_days == 30
    assert result.calculation.combined_rate_applied is True
    maternity = next(item for item in result.calculation.leaves if item.leave_type == "macierzynski")
    assert maternity.weeks == 20
    assert maternity.rate_percent == 81.5


def test_open_question_cites_legal_basis(params):
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
    assert "Podstawa prawna" in response.answer or any(
        item.legal_basis in (response.answer or "") for item in response.citations
    )


def test_graph_search_finds_waiting_period():
    hits = GraphService().search("ile dni wyczekiwania na umowie zlecenie")
    assert "ryzyko_wyczekiwanie_90" in hits or "przepis_wyczekiwanie" in hits
