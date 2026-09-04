import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_post_route_v2_endpoint():
    response = client.post("/route/v2", json={"start": "A", "destination": "F"})
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == ["A", "D", "E", "F"]
    assert data["distance"] == 9.0


def test_post_route_astar_endpoint():
    response = client.post("/route/astar", json={"start": "A", "destination": "F"})
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == ["A", "D", "E", "F"]
    assert data["distance"] == 9.0


def test_post_route_v2_invalid_node():
    response = client.post("/route/v2", json={"start": "INVALID", "destination": "F"})
    assert response.status_code == 404
