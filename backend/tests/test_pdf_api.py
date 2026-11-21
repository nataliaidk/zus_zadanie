from tests.pdf_fixtures import ZAM_LINES, make_pdf


def test_pdf_upload_endpoint(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    response = client.post(
        "/api/pdf/calculate",
        files={"file": ("zam.pdf", make_pdf(ZAM_LINES), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_code"] == "ZAM"
    assert body["extraction_method"] == "regex"
    assert body["calculation"]["waiting_period_days"] == 30


def test_pdf_rejects_non_pdf(client):
    response = client.post(
        "/api/pdf/calculate",
        files={"file": ("notes.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_chat_endpoint_start_and_question(client):
    start = client.post("/api/chat", json={"action": "start"})
    assert start.status_code == 200
    body = start.json()
    assert body["buttons"]
    asked = client.post(
        "/api/chat",
        json={
            "session_id": body["session_id"],
            "action": "question",
            "message": "Co to jest wniosek ZAM?",
        },
    )
    assert asked.status_code == 200
    assert asked.json()["citations"]
    assert all(item["legal_basis"] for item in asked.json()["citations"])
