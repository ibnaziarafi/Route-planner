"""
Standalone test script for the PDP solver in backend/pdp/.
Validates both the user's toy example and a 10-driver / 50-order scale scenario.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

import time
import random
from backend.pdp.models import Driver, Order, StopType
from backend.pdp.distance_matrix import DistanceMatrix, default_single_source_dijkstra
from backend.pdp.scratch_solver import solve as scratch_solve
from backend.pdp.pdp_service import PDPService
from backend.graph.graph import Graph


def test_toy_example():
    print("=== TEST 1: TOY EXAMPLE (2 Drivers, 4 Orders) ===")

    graph_data = {
        "A": {"B": 4, "C": 2},
        "B": {"A": 4, "D": 5, "E": 10},
        "C": {"A": 2, "D": 8, "F": 4},
        "D": {"B": 5, "C": 8, "G": 6},
        "E": {"B": 10, "H": 3},
        "F": {"C": 4, "I": 7},
        "G": {"D": 6, "H": 2, "I": 5},
        "H": {"E": 3, "G": 2, "J": 4},
        "I": {"F": 7, "G": 5, "J": 3},
        "J": {"H": 4, "I": 3},
    }

    graph = Graph()
    for u, neighbors in graph_data.items():
        for v, weight in neighbors.items():
            graph.add_edge(u, v, weight, bidirectional=False)

    drivers = [
        Driver(driver_id=1, start_node="A", capacity=3),
        Driver(driver_id=2, start_node="E", capacity=3),
    ]

    orders = [
        Order(order_id=101, pickup_node="C", dropoff_node="H"),
        Order(order_id=102, pickup_node="F", dropoff_node="I"),
        Order(order_id=103, pickup_node="D", dropoff_node="J"),
        Order(order_id=104, pickup_node="B", dropoff_node="G"),
    ]

    relevant_nodes = sorted(
        {d.start_node for d in drivers}
        | {o.pickup_node for o in orders}
        | {o.dropoff_node for o in orders}
    )

    dm = DistanceMatrix(relevant_nodes, graph, default_single_source_dijkstra)
    solution = scratch_solve(orders, drivers, dm)

    for route in solution.routes.values():
        print(f"Driver {route.driver_id} (dist={route.total_distance:.1f}): {route.stops}")
    print(f"Unassigned: {solution.unassigned_orders}")
    print(f"TOTAL DISTANCE: {solution.total_distance:.1f}")

    assert len(solution.unassigned_orders) == 0, "All orders should be assigned"
    assert solution.total_distance > 0, "Distance should be positive"

    # Assert Pickup happens before Dropoff for every order
    for route in solution.routes.values():
        pickups = {}
        dropoffs = {}
        for idx, stop in enumerate(route.stops):
            if stop.stop_type == StopType.PICKUP:
                pickups[stop.order_id] = idx
            else:
                dropoffs[stop.order_id] = idx

        for order_id in pickups:
            assert order_id in dropoffs, f"Order {order_id} dropped off"
            assert pickups[order_id] < dropoffs[order_id], (
                f"Pickup of order {order_id} at index {pickups[order_id]} must precede dropoff at {dropoffs[order_id]}"
            )

    print("Toy example test PASSED!\n")


def test_scale_example():
    print("=== TEST 2: SCALE TEST (10 Drivers, 50 Orders) ===")

    # Create a grid/random graph with 40 nodes (N1 to N40)
    node_names = [f"N{i}" for i in range(1, 41)]
    graph = Graph()

    random.seed(42)
    # Add random connected edges
    for i in range(len(node_names)):
        u = node_names[i]
        # Connect to next 3 nodes with random weights
        for j in range(1, 4):
            v = node_names[(i + j) % len(node_names)]
            weight = random.randint(3, 15)
            graph.add_edge(u, v, weight, bidirectional=True)

    drivers = [
        Driver(driver_id=i, start_node=random.choice(node_names), capacity=5)
        for i in range(1, 11)
    ]

    orders = [
        Order(
            order_id=100 + i,
            pickup_node=random.choice(node_names),
            dropoff_node=random.choice(node_names),
            demand=1
        )
        for i in range(1, 51)
    ]

    # Filter out orders where pickup == dropoff for realism
    orders = [o for o in orders if o.pickup_node != o.dropoff_node]

    relevant_nodes = sorted(
        {d.start_node for d in drivers}
        | {o.pickup_node for o in orders}
        | {o.dropoff_node for o in orders}
    )

    start_time = time.time()
    dm = DistanceMatrix(relevant_nodes, graph, default_single_source_dijkstra)
    matrix_time = time.time() - start_time

    solve_start = time.time()
    solution = scratch_solve(orders, drivers, dm)
    solve_time = time.time() - solve_start

    print(f"Matrix Build Time: {matrix_time * 1000:.2f} ms")
    print(f"Solver Time: {solve_time * 1000:.2f} ms")
    print(f"Total Assigned Orders: {sum(len(r.stops)//2 for r in solution.routes.values())}/{len(orders)}")
    print(f"Unassigned Orders: {len(solution.unassigned_orders)}")
    print(f"Total Fleet Distance: {solution.total_distance:.1f}")

    # Verify constraints across all 10 drivers
    for route in solution.routes.values():
        pickups = {}
        dropoffs = {}
        for idx, stop in enumerate(route.stops):
            if stop.stop_type == StopType.PICKUP:
                pickups[stop.order_id] = idx
            else:
                dropoffs[stop.order_id] = idx

        for order_id in pickups:
            assert order_id in dropoffs, f"Order {order_id} must have a dropoff"
            assert pickups[order_id] < dropoffs[order_id], (
                f"Pickup of order {order_id} at {pickups[order_id]} must come before dropoff at {dropoffs[order_id]}"
            )

    print("10 Drivers / 50 Orders Scale Test PASSED!\n")


if __name__ == "__main__":
    test_toy_example()
    test_scale_example()
