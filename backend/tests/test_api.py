import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_graph_endpoint():
    response = client.get("/graph")
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert "positions" in data
    assert "A" in data["nodes"]
    assert len(data["edges"]) == 7

def test_post_route_endpoint():
    response = client.post("/route", json={"start": "A", "destination": "F"})
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == ["A", "D", "E", "F"]
    assert data["distance"] == 9.0

def test_post_multi_stop_route_endpoint():
    response = client.post(
        "/route/multi-stop",
        json={"start": "A", "stops": ["D", "C"], "destination": "F"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "route" in data
    assert data["route"][0] == "A"
    assert data["route"][-1] == "F"
    assert data["distance"] > 0
