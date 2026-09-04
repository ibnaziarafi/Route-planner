import pytest
from backend.graph.graph_data import create_default_graph, NODE_POSITIONS
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.algorithms.astar import astar


def test_astar_routes_a_to_f():
    graph = create_default_graph()
    path, distance = astar(graph, "A", "F", NODE_POSITIONS)
    v2_path, v2_distance = dijkstra_v2(graph, "A", "F")

    assert distance == v2_distance == 9.0
    assert path == v2_path == ["A", "D", "E", "F"]


def test_astar_routes_a_to_c():
    graph = create_default_graph()
    path, distance = astar(graph, "A", "C", NODE_POSITIONS)
    v2_path, v2_distance = dijkstra_v2(graph, "A", "C")

    assert distance == v2_distance == 8.0
    assert path == ["A", "B", "C"]


def test_astar_routes_d_to_c():
    graph = create_default_graph()
    path, distance = astar(graph, "D", "C", NODE_POSITIONS)
    v2_path, v2_distance = dijkstra_v2(graph, "D", "C")

    assert distance == v2_distance == 9.0
    assert path == ["D", "E", "F", "C"]


def test_astar_routes_b_to_f():
    graph = create_default_graph()
    path, distance = astar(graph, "B", "F", NODE_POSITIONS)
    v2_path, v2_distance = dijkstra_v2(graph, "B", "F")

    assert distance == v2_distance == 5.0
    assert path == ["B", "C", "F"]


def test_astar_same_start_and_destination():
    graph = create_default_graph()
    path, distance = astar(graph, "A", "A", NODE_POSITIONS)
    assert path == ["A"]
    assert distance == 0.0


def test_astar_unreachable_node():
    graph = create_default_graph()
    graph.add_node("ISLAND")
    path, distance = astar(graph, "A", "ISLAND", NODE_POSITIONS)
    assert path == []
    assert distance == float('inf')


def test_astar_invalid_node():
    graph = create_default_graph()
    path, distance = astar(graph, "INVALID", "F", NODE_POSITIONS)
    assert path == []
    assert distance == float('inf')
