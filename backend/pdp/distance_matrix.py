"""
Bridges your existing graph + Dijkstra/A* code to the routing layer.

The routing algorithms never touch your graph directly. They only ever ask
"what's the cost from location i to location j?" via a plain 2D matrix. This
module is the only place that talks to your graph.

IMPORTANT for performance: don't call Dijkstra separately for every
(source, dest) pair. Dijkstra naturally computes shortest distances from ONE
source to ALL other nodes in a single run. So to build a full matrix over N
relevant nodes, you should run Dijkstra N times (once per relevant node as
source), not N*N times.
"""

from typing import Callable, Optional
import heapq


def default_single_source_dijkstra(graph, source_node: str) -> dict[str, float]:
    """
    Computes shortest path distances from source_node to all reachable nodes in `graph`.
    Uses binary min-heap for O((V + E) log V) efficiency.
    Compatible with backend.graph.graph.Graph interface.
    """
    if hasattr(graph, "has_node") and not graph.has_node(source_node):
        return {source_node: 0.0}

    nodes = graph.get_nodes() if hasattr(graph, "get_nodes") else list(graph.keys())
    dist = {node: float("inf") for node in nodes}
    dist[source_node] = 0.0

    pq = [(0.0, source_node)]

    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue

        neighbors = graph.get_neighbors(u) if hasattr(graph, "get_neighbors") else graph[u].items()
        for v, weight in neighbors:
            nd = d + weight
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))

    return dist


class DistanceMatrix:
    """
    node_ids: every location that matters for this routing problem
              (all driver start nodes + all pickup nodes + all dropoff nodes).
    single_source_shortest_paths: function with signature (graph, source_node) -> dict[node_id, distance].
    """

    def __init__(
        self,
        node_ids: list[str],
        graph,
        single_source_shortest_paths: Optional[Callable[[object, str], dict[str, float]]] = None,
    ):
        if single_source_shortest_paths is None:
            single_source_shortest_paths = default_single_source_dijkstra

        self.index_of = {node: i for i, node in enumerate(node_ids)}
        self.nodes = node_ids
        n = len(node_ids)
        self.matrix = [[0.0] * n for _ in range(n)]

        for i, source in enumerate(node_ids):
            distances = single_source_shortest_paths(graph, source)
            for j, target in enumerate(node_ids):
                if i == j:
                    continue
                d = distances.get(target)
                if d is None:
                    # Unreachable -- use sentinel
                    d = float("inf")
                self.matrix[i][j] = d

    def cost(self, a: str, b: str) -> float:
        return self.matrix[self.index_of[a]][self.index_of[b]]
