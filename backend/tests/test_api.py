from app.services.graph_service import GraphService


PROFILE = {
    "employment_form": "umowa_o_prace",
    "company_insured_above_20": False,
    "birth_date": "2026-11-01",
    "number_of_children": 1,
    "request_days_after_birth": 10,
}


def test_calculate_endpoint(client):
    response = client.post("/api/calculate", json=PROFILE)
    assert response.status_code == 200
    body = response.json()
    assert body["waiting_period_days"] == 30
    assert body["combined_rate_applied"] is True
    assert any(doc["code"] == "ZAM" and doc["active"] for doc in body["documents"])
    assert not any(doc["code"] in {"ZUR", "ZAO", "Z-3b"} and doc["active"] for doc in body["documents"])


def test_graph_dump(client):
    response = client.get("/api/graph")
    assert response.status_code == 200
    body = response.json()
    assert len(body["nodes"]) > 10
    assert len(body["edges"]) > 10
    types = {node["type"] for node in body["nodes"]}
    assert "przepis" in types
    assert "swiadczenie" in types


def test_graph_explain_get(client):
    response = client.get(
        "/api/graph/explain",
        params={"node_id": "swiadczenie_macierzynski"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["question"] == "Skąd ten wynik?"
    assert "przepis_kodeks_pracy" in body["path"]
    assert body["nodes"]


def test_graph_explain_post_path(client):
    response = client.post(
        "/api/graph/explain",
        json={
            "node_id": "przepis_formularze_zam",
            "target_id": "dokument_zam",
        },
    )
    assert response.status_code == 200
    assert response.json()["path"] == ["przepis_formularze_zam", "dokument_zam"]


def test_graph_explain_unknown_node(client):
    response = client.get("/api/graph/explain", params={"node_id": "nie_ma"})
    assert response.status_code == 404


def test_admin_params_get_put_roundtrip(client):
    original = client.get("/api/admin/params")
    assert original.status_code == 200
    payload = original.json()
    try:
        payload["rates_percent"]["parental"] = 70.0
        put = client.put("/api/admin/params", json=payload)
        assert put.status_code == 200
        assert put.json()["legal_as_of"] == "2026-11"
        assert put.json()["rates_percent"]["parental"] == 70.0
    finally:
        restore = client.put("/api/admin/params", json=original.json())
        assert restore.status_code == 200


def test_graph_has_required_node_types():
    graph = GraphService().graph
    types = {data["type"] for _, data in graph.nodes(data=True)}
    assert types == {
        "status_ubezpieczenia",
        "zdarzenie",
        "swiadczenie",
        "dokument",
        "ryzyko",
        "przepis",
    }
    for _, data in graph.nodes(data=True):
        assert data.get("plain_language")
        assert data.get("legal_basis")
        assert data.get("title")
