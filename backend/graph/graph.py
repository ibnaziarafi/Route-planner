class Graph:
    """
    Adjacency list representation of a weighted, undirected graph.
    """
    def __init__(self):
        # adj mapping: node_name -> list of tuples (neighbor_name, weight)
        self.adj = {}

    def add_node(self, node: str) -> None:
        """Adds a node to the graph if it doesn't already exist."""
        if node not in self.adj:
            self.adj[node] = []

    def add_edge(self, u: str, v: str, weight: float, bidirectional: bool = True) -> None:
        """
        Adds a weighted edge between node u and node v.
        Creates nodes u and v if they do not exist.
        """
        self.add_node(u)
        self.add_node(v)
        
        # Check if edge u -> v already exists, update weight if so, else append
        self._add_or_update_neighbor(u, v, weight)
        if bidirectional:
            self._add_or_update_neighbor(v, u, weight)

    def _add_or_update_neighbor(self, src: str, dest: str, weight: float) -> None:
        for i, (neighbor, _) in enumerate(self.adj[src]):
            if neighbor == dest:
                self.adj[src][i] = (dest, weight)
                return
        self.adj[src].append((dest, weight))

    def get_neighbors(self, node: str) -> list[tuple[str, float]]:
        """Returns the list of (neighbor, weight) tuples for a given node."""
        return self.adj.get(node, [])

    def get_nodes(self) -> list[str]:
        """Returns a list of all node identifiers in sorted order."""
        return sorted(list(self.adj.keys()))

    def get_edges(self) -> list[dict]:
        """Returns a list of all unique edges with u, v, weight."""
        edges = []
        seen = set()
        for u in self.adj:
            for v, weight in self.adj[u]:
                edge_key = tuple(sorted([u, v]))
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append({"u": u, "v": v, "weight": weight})
        return edges

    def has_node(self, node: str) -> bool:
        """Returns True if the node exists in the graph."""
        return node in self.adj
