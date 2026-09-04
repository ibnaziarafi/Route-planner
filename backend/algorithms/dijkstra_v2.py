from typing import TYPE_CHECKING
from backend.structures.min_heap import MinHeap

if TYPE_CHECKING:
    from backend.graph.graph import Graph


def dijkstra_v2(graph: "Graph", start: str, destination: str) -> tuple[list[str], float]:
    """
    Computes the shortest path between `start` and `destination` using Dijkstra's algorithm
    optimized with a custom MinHeap.

    Returns a tuple of (path_as_list_of_nodes, total_distance).
    If unreachable or invalid, returns ([], float('inf')).
    """
    # 1. Check if start and destination nodes exist in the graph
    if not graph.has_node(start) or not graph.has_node(destination):
        return [], float('inf')

    # 2. Edge case: start node is the destination node
    if start == destination:
        return [start], 0.0

    nodes = graph.get_nodes()

    # 3. Initialize distance table and previous node tracker
    distances = {node: float('inf') for node in nodes}
    previous = {node: None for node in nodes}

    distances[start] = 0.0

    # 4. Initialize custom MinHeap and push starting node
    min_heap = MinHeap()
    min_heap.push(0.0, start)

    while not min_heap.is_empty():
        current_dist, current = min_heap.pop()

        # If we popped a distance greater than the recorded shortest distance, skip (outdated entry)
        if current_dist > distances[current]:
            continue

        # Early termination: if we reached destination node, stop processing
        if current == destination:
            break

        # Explore neighbors
        for neighbor, weight in graph.get_neighbors(current):
            new_dist = distances[current] + weight
            if new_dist < distances[neighbor]:
                distances[neighbor] = new_dist
                previous[neighbor] = current
                # Push updated shortest distance onto the priority queue (MinHeap)
                min_heap.push(new_dist, neighbor)

    # 5. Path reconstruction
    if distances[destination] == float('inf'):
        return [], float('inf')

    path = []
    curr = destination
    while curr is not None:
        path.append(curr)
        curr = previous[curr]

    path.reverse()
    return path, distances[destination]
