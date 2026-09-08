import networkx as nx
from fastapi.testclient import TestClient

from backend.algorithms.dijkstra import dijkstra
from backend.main import app
from backend.real_map import service as real_map_service
from backend.real_map.graph_adapter import OSMGraphAdapter
from backend.real_map.osm_graph import load_hobart_graph
from backend.real_map.service import calculate_real_map_route


def make_test_graph():
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=147.0, y=-42.0)
    graph.add_node(2, x=147.001, y=-42.001)
    graph.add_node(3, x=147.002, y=-42.002)
    graph.add_edge(1, 2, length=10)
    graph.add_edge(2, 3, length=20)
    return graph


def test_adapter_preserves_directed_length_weights():
    adapter = OSMGraphAdapter(make_test_graph())

    assert adapter.get_nodes() == ["1", "2", "3"]
    assert adapter.get_neighbors("1") == [("2", 10.0)]
    assert adapter.get_neighbors("3") == []
    assert dijkstra(adapter, "1", "3")[1] == 30.0


def test_cached_graph_loading(tmp_path):
    cache_path = tmp_path / "hobart_drive.graphml"
    nx.write_graphml(make_test_graph(), cache_path)

    loaded = load_hobart_graph(cache_path)

    assert set(loaded.nodes) == {"1", "2", "3"}
    assert loaded["1"]["2"]["length"] == 10


def test_real_map_service_dispatches_all_algorithms():
    adapter = OSMGraphAdapter(make_test_graph())

    for algorithm in ("dijkstra", "dijkstra_v2", "a_star"):
        result = calculate_real_map_route(
            type("Request", (), {
                "start_lat": -42.0,
                "start_lon": 147.0,
                "end_lat": -42.002,
                "end_lon": 147.002,
                "algorithm": algorithm,
            })(),
            graph=adapter,
        )
        assert result["algorithm"] == algorithm
        assert result["distance"] == 30.0
        assert [point["node"] for point in result["path"]] == ["1", "2", "3"]


def test_real_map_api_uses_cached_adapter(monkeypatch):
    adapter = OSMGraphAdapter(make_test_graph())
    monkeypatch.setattr(real_map_service, "get_hobart_adapter", lambda: adapter)
    client = TestClient(app)

    response = client.post(
        "/api/real-map/route",
        json={
            "start_lat": -42.0,
            "start_lon": 147.0,
            "end_lat": -42.002,
            "end_lon": 147.002,
            "algorithm": "dijkstra_v2",
        },
    )

    assert response.status_code == 200
    assert response.json()["distance"] == 30.0
    assert response.json()["path"][-1]["node"] == "3"


def test_real_map_api_rejects_invalid_algorithm():
    client = TestClient(app)
    response = client.post(
        "/api/real-map/route",
        json={
            "start_lat": -42.0,
            "start_lon": 147.0,
            "end_lat": -42.002,
            "end_lon": 147.002,
            "algorithm": "not-an-algorithm",
        },
    )

    assert response.status_code == 422


def test_adapter_rejects_locations_outside_cached_extent():
    adapter = OSMGraphAdapter(make_test_graph())

    assert adapter.nearest_node(-40.0, 147.0) is None
