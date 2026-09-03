from backend.graph.graph import Graph

# Node visual positions (2D canvas coordinates)
NODE_POSITIONS = {
    "A": {"x": 100, "y": 100},
    "B": {"x": 350, "y": 100},
    "C": {"x": 600, "y": 100},
    "D": {"x": 100, "y": 300},
    "E": {"x": 350, "y": 300},
    "F": {"x": 600, "y": 300},
}

def create_default_graph() -> Graph:
    """
    Creates and populates the default graph according to Phase 1 specification:
    A - B: 5,  A - D: 2
    B - C: 3,  B - E: 4
    C - F: 2
    D - E: 6
    E - F: 1
    """
    g = Graph()
    g.add_edge("A", "B", 5)
    g.add_edge("A", "D", 2)
    g.add_edge("B", "C", 3)
    g.add_edge("B", "E", 4)
    g.add_edge("C", "F", 2)
    g.add_edge("D", "E", 6)
    g.add_edge("E", "F", 1)
    return g
