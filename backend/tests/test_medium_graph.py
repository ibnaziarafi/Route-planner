import pytest
from fastapi.testclient import TestClient
from backend.graph.graph_data import create_medium_graph, MEDIUM_NODE_POSITIONS
from backend.algorithms.dijkstra import dijkstra
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.algorithms.astar import astar
from backend.main import app

client = TestClient(app)


def test_medium_graph_node_count():
    g = create_medium_graph()
    nodes = g.get_nodes()
    assert len(nodes) == 20
    assert nodes[0] == "A"
    assert nodes[-1] == "T"
    assert len(MEDIUM_NODE_POSITIONS) == 20


def test_medium_graph_pathfinding_equivalence():
    g = create_medium_graph()
    p1, d1 = dijkstra(g, "A", "T")
    p2, d2 = dijkstra_v2(g, "A", "T")
    p_ast, d_ast = astar(g, "A", "T", MEDIUM_NODE_POSITIONS)

    assert d1 == d2 == d_ast
    assert len(p1) > 0
    assert p1[0] == "A"
    assert p1[-1] == "T"


def test_medium_graph_api_endpoint():
    response = client.get("/graph?graph_type=medium")
    assert response.status_code == 200
    data = response.json()
    assert len(data["nodes"]) == 20
    assert "T" in data["nodes"]

    route_res = client.post("/route/v2", json={"start": "A", "destination": "T", "graph_type": "medium"})
    assert route_res.status_code == 200
    r_data = route_res.json()
    assert r_data["path"][0] == "A"
    assert r_data["path"][-1] == "T"
    assert r_data["distance"] > 0
