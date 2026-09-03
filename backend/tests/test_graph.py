import pytest
from backend.graph.graph import Graph
from backend.graph.graph_data import create_default_graph

def test_graph_node_and_edge_creation():
    g = Graph()
    g.add_node("A")
    g.add_node("B")
    g.add_edge("A", "B", 7)

    assert g.has_node("A")
    assert g.has_node("B")
    assert g.get_neighbors("A") == [("B", 7)]
    assert g.get_neighbors("B") == [("A", 7)]

def test_graph_edge_weight_update():
    g = Graph()
    g.add_edge("A", "B", 5)
    g.add_edge("A", "B", 10)  # Update weight
    assert g.get_neighbors("A") == [("B", 10)]

def test_default_graph_structure():
    g = create_default_graph()
    nodes = g.get_nodes()
    assert nodes == ["A", "B", "C", "D", "E", "F"]
    
    # Check neighbors of A
    neighbors_a = dict(g.get_neighbors("A"))
    assert neighbors_a == {"B": 5, "D": 2}
    
    # Check edges
    edges = g.get_edges()
    assert len(edges) == 7
