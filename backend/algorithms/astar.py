from typing import TYPE_CHECKING, Any
from backend.structures.min_heap import MinHeap
from backend.algorithms.heuristics import euclidean_distance

if TYPE_CHECKING:
    from backend.graph.graph import Graph


def astar(
    graph: "Graph",
    start: str,
    destination: str,
    positions: dict[str, Any]
) -> tuple[list[str], float]:
    """
    Computes the shortest path between `start` and `destination` using the A* algorithm
    guided by a geographic Euclidean heuristic and powered by a custom MinHeap.

    Returns a tuple of (path_as_list_of_nodes, total_actual_distance).
    If unreachable or invalid, returns ([], float('inf')).
    """
    # 1. Check if start and destination exist in the graph
    if not graph.has_node(start) or not graph.has_node(destination):
        return [], float('inf')

    # 2. Edge case: start node is destination node
    if start == destination:
        return [start], 0.0

    nodes = graph.get_nodes()

    # 3. g_score[node] stores exact actual distance from start to node
    g_score = {node: float('inf') for node in nodes}
    previous = {node: None for node in nodes}

    g_score[start] = 0.0

    # 4. f(start) = g(start) + h(start, destination)
    h_start = euclidean_distance(start, destination, positions)
    f_start = g_score[start] + h_start

    min_heap = MinHeap()
    min_heap.push(f_start, start)

    while not min_heap.is_empty():
        current_f, current = min_heap.pop()

        # Stop early if destination reached
        if current == destination:
            break

        # Calculate current heuristic to check for stale entries in priority queue
        h_curr = euclidean_distance(current, destination, positions)
        if current_f > g_score[current] + h_curr:
            continue

        # Explore neighbors
        for neighbor, weight in graph.get_neighbors(current):
            tentative_g = g_score[current] + weight

            if tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                previous[neighbor] = current

                # f(n) = g(n) + h(n)
                h_neighbor = euclidean_distance(neighbor, destination, positions)
                f_neighbor = tentative_g + h_neighbor

                min_heap.push(f_neighbor, neighbor)

    # 5. Path reconstruction
    if g_score[destination] == float('inf'):
        return [], float('inf')

    path = []
    curr = destination
    while curr is not None:
        path.append(curr)
        curr = previous[curr]

    path.reverse()
    return path, g_score[destination]
