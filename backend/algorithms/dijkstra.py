from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.graph.graph import Graph

def dijkstra(graph: "Graph", start: str, destination: str) -> tuple[list[str], float]:
    """
    Computes the shortest path between `start` and `destination` using Dijkstra's algorithm.
    Returns a tuple of (path_as_list_of_nodes, total_distance).
    If unreachable or invalid, returns ([], float('inf')).
    """
    # Check if nodes exist in graph
    if not graph.has_node(start) or not graph.has_node(destination):
        return [], float('inf')

    # Edge case: start is destination
    if start == destination:
        return [start], 0.0

    nodes = graph.get_nodes()
    
    # Initialize distances and previous node maps
    distances = {node: float('inf') for node in nodes}
    previous = {node: None for node in nodes}
    unvisited = set(nodes)

    distances[start] = 0.0

    while unvisited:
        # Find unvisited node with the smallest distance
        current = None
        current_dist = float('inf')
        for node in unvisited:
            if distances[node] < current_dist:
                current_dist = distances[node]
                current = node

        # If smallest distance is infinity or no current node, remaining nodes unreachable
        if current is None or current_dist == float('inf'):
            break

        # Stop early if destination reached
        if current == destination:
            break

        unvisited.remove(current)

        # Update distances of neighbors
        for neighbor, weight in graph.get_neighbors(current):
            if neighbor in unvisited:
                new_dist = distances[current] + weight
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current

    # Reconstruct path from destination to start
    if distances[destination] == float('inf'):
        return [], float('inf')

    path = []
    curr = destination
    while curr is not None:
        path.append(curr)
        curr = previous[curr]

    path.reverse()
    return path, distances[destination]
