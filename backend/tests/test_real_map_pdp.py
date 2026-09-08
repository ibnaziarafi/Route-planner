from types import SimpleNamespace

import networkx as nx
from fastapi.testclient import TestClient

from backend.main import app
from backend.real_map.graph_adapter import OSMGraphAdapter
from backend.real_map_pdp.real_map_pdp_service import solve_real_map_pdp
from backend.real_map_pdp.schemas import RealMapPDPRequest


def make_graph():
    graph = nx.MultiDiGraph()
    for node, lon, lat in ((1, 147.0, -42.0), (2, 147.001, -42.001), (3, 147.002, -42.002), (4, 147.003, -42.003)):
        graph.add_node(node, x=lon, y=lat)
    graph.add_edge(1, 2, length=10)
    graph.add_edge(2, 3, length=20)
    graph.add_edge(3, 4, length=30)
    graph.add_edge(2, 1, length=10)
    graph.add_edge(3, 2, length=20)
    graph.add_edge(4, 3, length=30)
    return OSMGraphAdapter(graph)


def request(**overrides):
    values = {
        "drivers": [{"driver_id": 1, "start_lat": -42.0, "start_lon": 147.0, "capacity": 1}],
        "orders": [{"order_id": 1, "pickup_lat": -42.001, "pickup_lon": 147.001, "dropoff_lat": -42.003, "dropoff_lon": 147.003}],
        "algorithm": "dijkstra_v2",
        "solver": "scratch",
        "time_limit_seconds": 1,
    }
    values.update(overrides)
    return RealMapPDPRequest(**values)


def test_real_map_pdp_expands_route_and_preserves_order():
    result = solve_real_map_pdp(request(), graph=make_graph())

    assert result["total_distance_km"] == 0.06
    assert result["unassigned_orders"] == []
    assert [stop["type"] for stop in result["routes"][0]["stops"]] == ["pickup", "dropoff"]
    assert [point["node"] for point in result["routes"][0]["full_path"]] == ["1", "2", "3", "4"]


def test_real_map_pdp_api_rejects_invalid_solver():
    client = TestClient(app)
    response = client.post(
        "/api/real-map-pdp/solve",
        json={
            "drivers": [{"driver_id": 1, "start_lat": -42, "start_lon": 147, "capacity": 1}],
            "orders": [],
            "solver": "invalid",
        },
    )

    assert response.status_code == 422


def test_real_map_pdp_api_rejects_outside_map_coordinates(monkeypatch):
    from backend.real_map_pdp import real_map_pdp_service

    monkeypatch.setattr(real_map_pdp_service, "get_hobart_adapter", lambda: make_graph())
    client = TestClient(app)
    response = client.post(
        "/api/real-map-pdp/solve",
        json={
            "drivers": [{"driver_id": 1, "start_lat": -10, "start_lon": 100, "capacity": 1}],
            "orders": [],
        },
    )

    assert response.status_code == 400


def test_real_map_pdp_supports_multiple_drivers_and_orders():
    result = solve_real_map_pdp(
        request(
            drivers=[
                {"driver_id": 1, "start_lat": -42.0, "start_lon": 147.0, "capacity": 1},
                {"driver_id": 2, "start_lat": -42.002, "start_lon": 147.002, "capacity": 1},
            ],
            orders=[
                {"order_id": 1, "pickup_lat": -42.001, "pickup_lon": 147.001, "dropoff_lat": -42.003, "dropoff_lon": 147.003},
                {"order_id": 2, "pickup_lat": -42.003, "pickup_lon": 147.003, "dropoff_lat": -42.001, "dropoff_lon": 147.001},
            ],
        ),
        graph=make_graph(),
    )

    assert len(result["routes"]) == 2
    assert result["unassigned_orders"] == []
    for route in result["routes"]:
        open_orders = set()
        for stop in route["stops"]:
            if stop["type"] == "pickup":
                open_orders.add(stop["order_id"])
            else:
                assert stop["order_id"] in open_orders
                open_orders.remove(stop["order_id"])
        assert not open_orders
