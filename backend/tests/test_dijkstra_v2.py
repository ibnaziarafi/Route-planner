import pytest
from backend.graph.graph import Graph
from backend.graph.graph_data import create_default_graph
from backend.algorithms.dijkstra import dijkstra
from backend.algorithms.dijkstra_v2 import dijkstra_v2


def test_dijkstra_v2_shortest_path_a_to_f():
    graph = create_default_graph()
    path, distance = dijkstra_v2(graph, "A", "F")
    assert path == ["A", "D", "E", "F"]
    assert distance == 9.0


def test_dijkstra_v2_same_start_and_destination():
    graph = create_default_graph()
    path, distance = dijkstra_v2(graph, "A", "A")
    assert path == ["A"]
    assert distance == 0.0


def test_dijkstra_v2_unreachable_destination():
    graph = create_default_graph()
    graph.add_node("ISLAND")  # Disconnected node
    path, distance = dijkstra_v2(graph, "A", "ISLAND")
    assert path == []
    assert distance == float('inf')


def test_dijkstra_v2_invalid_node():
    graph = create_default_graph()
    path, distance = dijkstra_v2(graph, "NON_EXISTENT", "F")
    assert path == []
    assert distance == float('inf')


def test_dijkstra_v1_vs_v2_equivalence():
    """
    Critical test: verify that dijkstra (V1) and dijkstra_v2 (V2) return
    the exact same path and distance for all node pairs in the default graph.
    """
    graph = create_default_graph()
    nodes = graph.get_nodes()

    for start in nodes:
        for dest in nodes:
            path1, dist1 = dijkstra(graph, start, dest)
            path2, dist2 = dijkstra_v2(graph, start, dest)
            assert path1 == path2, f"Path mismatch between V1 and V2 for {start} -> {dest}: {path1} vs {path2}"
            assert dist1 == dist2, f"Distance mismatch between V1 and V2 for {start} -> {dest}: {dist1} vs {dist2}"


def test_dijkstra_v1_vs_v2_custom_graph():
    g = Graph()
    g.add_edge("X", "Y", 10)
    g.add_edge("X", "Z", 2)
    g.add_edge("Z", "Y", 3)

    path1, dist1 = dijkstra(g, "X", "Y")
    path2, dist2 = dijkstra_v2(g, "X", "Y")

    assert path1 == ["X", "Z", "Y"]
    assert path2 == ["X", "Z", "Y"]
    assert dist1 == 5.0
    assert dist2 == 5.0
