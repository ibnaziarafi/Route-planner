import pytest
from backend.graph.graph import Graph
from backend.graph.graph_data import create_default_graph
from backend.algorithms.dijkstra import dijkstra

def test_dijkstra_shortest_path_a_to_f():
    graph = create_default_graph()
    path, distance = dijkstra(graph, "A", "F")
    assert path == ["A", "D", "E", "F"]
    assert distance == 9.0

def test_dijkstra_same_start_and_destination():
    graph = create_default_graph()
    path, distance = dijkstra(graph, "A", "A")
    assert path == ["A"]
    assert distance == 0.0

def test_dijkstra_unreachable_destination():
    graph = create_default_graph()
    graph.add_node("ISLAND")  # Disconnected node
    path, distance = dijkstra(graph, "A", "ISLAND")
    assert path == []
    assert distance == float('inf')

def test_dijkstra_invalid_node():
    graph = create_default_graph()
    path, distance = dijkstra(graph, "NON_EXISTENT", "F")
    assert path == []
    assert distance == float('inf')

def test_dijkstra_alternative_path():
    # Construct graph where direct route is heavier than multi-hop
    g = Graph()
    g.add_edge("X", "Y", 10)
    g.add_edge("X", "Z", 2)
    g.add_edge("Z", "Y", 3)
    path, distance = dijkstra(g, "X", "Y")
    assert path == ["X", "Z", "Y"]
    assert distance == 5.0
