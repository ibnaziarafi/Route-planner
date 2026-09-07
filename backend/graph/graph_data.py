from backend.graph.graph import Graph

# Phase 1 Small Graph Node visual positions (2D canvas coordinates)
NODE_POSITIONS = {
    "A": {"x": 100, "y": 100},
    "B": {"x": 350, "y": 100},
    "C": {"x": 600, "y": 100},
    "D": {"x": 100, "y": 300},
    "E": {"x": 350, "y": 300},
    "F": {"x": 600, "y": 300},
}

# Phase 2 Medium Graph Node visual positions (20 nodes: A through T in a 5x4 grid layout)
MEDIUM_NODE_POSITIONS = {
    "A": {"x": 100, "y": 100}, "B": {"x": 250, "y": 100}, "C": {"x": 400, "y": 100}, "D": {"x": 550, "y": 100}, "E": {"x": 700, "y": 100},
    "F": {"x": 100, "y": 220}, "G": {"x": 250, "y": 220}, "H": {"x": 400, "y": 220}, "I": {"x": 550, "y": 220}, "J": {"x": 700, "y": 220},
    "K": {"x": 100, "y": 340}, "L": {"x": 250, "y": 340}, "M": {"x": 400, "y": 340}, "N": {"x": 550, "y": 340}, "O": {"x": 700, "y": 340},
    "P": {"x": 100, "y": 460}, "Q": {"x": 250, "y": 460}, "R": {"x": 400, "y": 460}, "S": {"x": 550, "y": 460}, "T": {"x": 700, "y": 460},
}


def create_default_graph() -> Graph:
    """
    Creates and populates the default small graph according to Phase 1 specification:
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


def create_medium_graph() -> Graph:
    """
    Creates and populates a 20-node medium graph (A through T) with weighted edges.
    """
    g = Graph()
    # Row 1 Horizontal Edges
    g.add_edge("A", "B", 4)
    g.add_edge("B", "C", 3)
    g.add_edge("C", "D", 5)
    g.add_edge("D", "E", 2)

    # Row 2 Horizontal Edges
    g.add_edge("F", "G", 3)
    g.add_edge("G", "H", 4)
    g.add_edge("H", "I", 2)
    g.add_edge("I", "J", 6)

    # Row 3 Horizontal Edges
    g.add_edge("K", "L", 5)
    g.add_edge("L", "M", 2)
    g.add_edge("M", "N", 4)
    g.add_edge("N", "O", 3)

    # Row 4 Horizontal Edges
    g.add_edge("P", "Q", 3)
    g.add_edge("Q", "R", 5)
    g.add_edge("R", "S", 2)
    g.add_edge("S", "T", 4)

    # Vertical Edges (Row 1 -> Row 2)
    g.add_edge("A", "F", 3)
    g.add_edge("B", "G", 2)
    g.add_edge("C", "H", 6)
    g.add_edge("D", "I", 4)
    g.add_edge("E", "J", 3)

    # Vertical Edges (Row 2 -> Row 3)
    g.add_edge("F", "K", 4)
    g.add_edge("G", "L", 3)
    g.add_edge("H", "M", 5)
    g.add_edge("I", "N", 2)
    g.add_edge("J", "O", 5)

    # Vertical Edges (Row 3 -> Row 4)
    g.add_edge("K", "P", 2)
    g.add_edge("L", "Q", 4)
    g.add_edge("M", "R", 3)
    g.add_edge("N", "S", 5)
    g.add_edge("O", "T", 2)

    # Diagonal & Cross Connections
    g.add_edge("A", "G", 6)
    g.add_edge("C", "I", 5)
    g.add_edge("F", "L", 4)
    g.add_edge("H", "N", 3)
    g.add_edge("K", "Q", 5)
    g.add_edge("M", "S", 4)

    return g


def get_graph_and_positions(graph_type: str = "small") -> tuple[Graph, dict]:
    """
    Returns (graph_instance, positions_dict) for the specified graph size ('small' or 'medium').
    """
    if graph_type and graph_type.lower() == "medium":
        return create_medium_graph(), MEDIUM_NODE_POSITIONS
    return create_default_graph(), NODE_POSITIONS
