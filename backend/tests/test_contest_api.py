from tests.pdf_fixtures import make_pdf


def test_upload_zuzanna_pregnancy_sickness(client, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    response = client.post(
        "/api/pdf/calculate",
        files={
            "file": (
                "Zuzanna Le_zas. chorobowy w ciąży.pdf",
                make_pdf(["skan bez warstwy tekstu"]),
                "application/pdf",
            )
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["missing_fields"] == []
    assert body["document_code"] == "ZAS-53"
    assert body["profile"] is not None
    assert body["calculation"] is not None
    assert any(item["code"] == "chorobowy_ciaza" for item in body["calculation"]["pregnancy"])


def test_charities(client):
    response = client.get("/api/charities")
    assert response.status_code == 200
    body = response.json()
    assert any("stillbirth" in item["situations"] for item in body)


def test_samples_list_and_calculate(client):
    listed = client.get("/api/samples")
    assert listed.status_code == 200
    ids = {item["id"] for item in listed.json()}
    assert "zam-etat" in ids
    calc = client.post("/api/samples/za-zyciem/calculate")
    assert calc.status_code == 200
    body = calc.json()
    parental = next(item for item in body["calculation"]["leaves"] if item["leave_type"] == "rodzicielski")
    assert parental["weeks"] == 65


def test_sample_pdf(client):
    response = client.get("/api/samples/zam-etat/pdf")
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_sim_no_body(client):
    response = client.post("/api/sim/mobywatel")
    assert response.status_code == 200
    body = response.json()
    assert "SYMULACJA" in body["banner"]
    assert body["logged_in"] is True


def test_sim_unknown(client):
    response = client.post("/api/sim/nie-ma")
    assert response.status_code == 404
