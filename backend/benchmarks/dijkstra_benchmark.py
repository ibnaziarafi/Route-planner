import time
from backend.graph.graph import Graph
from backend.graph.graph_data import create_default_graph, NODE_POSITIONS
from backend.algorithms.dijkstra import dijkstra
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.algorithms.astar import astar


def build_large_grid_graph(rows: int = 20, cols: int = 20) -> tuple[Graph, dict[str, tuple[float, float]]]:
    """
    Constructs a 2D grid graph with (rows x cols) nodes for scaling tests,
    returning both the Graph object and a positions dictionary for A* heuristic calculations.
    """
    g = Graph()
    positions = {}
    for r in range(rows):
        for c in range(cols):
            curr_node = f"N_{r}_{c}"
            positions[curr_node] = (float(c * 10), float(r * 10))

            # Connect to right neighbor
            if c + 1 < cols:
                right_node = f"N_{r}_{c+1}"
                g.add_edge(curr_node, right_node, weight=1.0)
            # Connect to bottom neighbor
            if r + 1 < rows:
                bottom_node = f"N_{r+1}_{c}"
                g.add_edge(curr_node, bottom_node, weight=1.0)
    return g, positions


def run_benchmark(
    graph: Graph,
    start: str,
    destination: str,
    positions: dict,
    iterations: int = 1000,
    label: str = "Default Graph"
):
    print(f"\n==================================================")
    print(f" Benchmark: {label}")
    print(f" Nodes: {len(graph.get_nodes())} | Start: '{start}' -> Dest: '{destination}'")
    print(f" Iterations: {iterations}")
    print(f"==================================================")

    # 1. Benchmark Dijkstra V1 (Array scan)
    start_v1 = time.perf_counter()
    for _ in range(iterations):
        path_v1, dist_v1 = dijkstra(graph, start, destination)
    end_v1 = time.perf_counter()
    time_v1 = end_v1 - start_v1

    # 2. Benchmark Dijkstra V2 (MinHeap)
    start_v2 = time.perf_counter()
    for _ in range(iterations):
        path_v2, dist_v2 = dijkstra_v2(graph, start, destination)
    end_v2 = time.perf_counter()
    time_v2 = end_v2 - start_v2

    # 3. Benchmark A* Algorithm (MinHeap + Geographic Heuristic)
    start_astar = time.perf_counter()
    for _ in range(iterations):
        path_astar, dist_astar = astar(graph, start, destination, positions)
    end_astar = time.perf_counter()
    time_astar = end_astar - start_astar

    # Compute averages
    avg_v1_us = (time_v1 / iterations) * 1_000_000
    avg_v2_us = (time_v2 / iterations) * 1_000_000
    avg_astar_us = (time_astar / iterations) * 1_000_000

    print(f"\n1. Dijkstra V1 (Array Scan)")
    print(f"   Total Time : {time_v1:.6f} s")
    print(f"   Avg / Run  : {avg_v1_us:.2f} us")
    print(f"   Distance   : {dist_v1}")

    print(f"\n2. Dijkstra V2 (MinHeap)")
    print(f"   Total Time : {time_v2:.6f} s")
    print(f"   Avg / Run  : {avg_v2_us:.2f} us")
    print(f"   Distance   : {dist_v2}")

    print(f"\n3. A* Pathfinding (Geographic Heuristic)")
    print(f"   Total Time : {time_astar:.6f} s")
    print(f"   Avg / Run  : {avg_astar_us:.2f} us")
    print(f"   Distance   : {dist_astar}")

    # Results Verification
    dist_equal = (dist_v1 == dist_v2 == dist_astar)
    print(f"\nResults Verification:")
    print(f"   Distance Equivalence (V1 == V2 == A*) : {dist_equal}")
    print(f"   Path V1 == V2                          : {path_v1 == path_v2}")
    print(f"   Path V2 == A*                         : {path_v2 == path_astar}")


def main():
    print("Starting Dijkstra V1 vs Dijkstra V2 vs A* Performance Benchmark...")

    # Benchmark 1: Standard Phase 1 Graph
    default_g = create_default_graph()
    run_benchmark(
        default_g,
        start="A",
        destination="F",
        positions=NODE_POSITIONS,
        iterations=10000,
        label="Phase 1 Default Graph (6 Nodes)"
    )

    # Benchmark 2: Larger Synthetic Grid Graph (400 nodes)
    large_g, grid_positions = build_large_grid_graph(rows=20, cols=20)
    run_benchmark(
        large_g,
        start="N_0_0",
        destination="N_19_19",
        positions=grid_positions,
        iterations=100,
        label="Large Grid Graph (400 Nodes)"
    )


if __name__ == "__main__":
    main()
