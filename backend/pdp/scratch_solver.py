"""
From-scratch solver for the multi-driver Pickup-and-Delivery Problem.

Algorithm, in two phases (construction + local search improvement):

PHASE 1 -- Cheapest Insertion (construction)
    Process orders one at a time. For each order, try inserting its pickup
    stop and dropoff stop into every driver's current route, at every valid
    position pair (pickup must come before its own dropoff; both must
    respect capacity). Keep whichever (driver, position) combo adds the
    least extra distance. Greedily builds a valid solution fast --
    O(orders x drivers x route_length^2), running in milliseconds at scale
    (e.g., 50 orders, 10 drivers).

PHASE 2 -- Or-opt local search (improvement)
    Repeatedly try relocating single order pairs (pickup+dropoff moved together)
    to a cheaper position, across drivers, as long as precedence and capacity still
    hold. Stop when no move improves total distance.
"""

from copy import deepcopy

from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType
from backend.pdp.distance_matrix import DistanceMatrix


def route_distance(route: Route, dm: DistanceMatrix, start_node: str) -> float:
    if not route.stops:
        return 0.0
    total = dm.cost(start_node, route.stops[0].node)
    for a, b in zip(route.stops, route.stops[1:]):
        total += dm.cost(a.node, b.node)
    return total


def _current_load_after(route: Route, upto_index: int, orders: dict[int, Order]) -> int:
    """How many items the driver is carrying right after stop `upto_index`."""
    load = 0
    for stop in route.stops[: upto_index + 1]:
        demand = orders[stop.order_id].demand
        load += demand if stop.stop_type == StopType.PICKUP else -demand
    return load


def _try_insert_order(
    route: Route,
    driver: Driver,
    order: Order,
    dm: DistanceMatrix,
    orders: dict[int, Order],
) -> tuple[float, Route] | None:
    """
    Find the cheapest way to insert this order's pickup+dropoff pair into
    `route`, respecting: pickup-before-dropoff, and capacity never exceeded.
    Returns (added_cost, new_route) or None if no valid insertion exists.
    """
    best_cost = float("inf")
    best_route = None
    n = len(route.stops)

    for pickup_pos in range(n + 1):
        for dropoff_pos in range(pickup_pos, n + 1):
            candidate = deepcopy(route)
            candidate.stops.insert(
                pickup_pos, Stop(order.order_id, order.pickup_node, StopType.PICKUP)
            )
            # dropoff index shifts by 1 because we just inserted the pickup
            candidate.stops.insert(
                dropoff_pos + 1, Stop(order.order_id, order.dropoff_node, StopType.DROPOFF)
            )

            # Capacity check across the whole route
            load = 0
            capacity_ok = True
            for stop in candidate.stops:
                demand = orders[stop.order_id].demand
                load += demand if stop.stop_type == StopType.PICKUP else -demand
                if load > driver.capacity:
                    capacity_ok = False
                    break
            if not capacity_ok:
                continue

            new_dist = route_distance(candidate, dm, driver.start_node)
            added = new_dist - route.total_distance
            if added < best_cost:
                best_cost = added
                candidate.total_distance = new_dist
                best_route = candidate

    if best_route is None:
        return None
    return best_cost, best_route


def build_initial_solution(
    orders: list[Order],
    drivers: list[Driver],
    dm: DistanceMatrix,
) -> Solution:
    routes = {d.driver_id: Route(driver_id=d.driver_id) for d in drivers}
    order_by_id = {o.order_id: o for o in orders}
    unassigned = []

    # Orders sorted by distance-from-nearest-driver first tends to produce
    # tighter routes than processing in arbitrary/input order.
    def nearest_driver_dist(o: Order) -> float:
        return min(dm.cost(d.start_node, o.pickup_node) for d in drivers)

    for order in sorted(orders, key=nearest_driver_dist):
        best_choice = None  # (added_cost, driver_id, new_route)
        for driver in drivers:
            result = _try_insert_order(
                routes[driver.driver_id], driver, order, dm, order_by_id
            )
            if result is None:
                continue
            added_cost, candidate_route = result
            if best_choice is None or added_cost < best_choice[0]:
                best_choice = (added_cost, driver.driver_id, candidate_route)

        if best_choice is None:
            unassigned.append(order.order_id)
        else:
            _, driver_id, new_route = best_choice
            routes[driver_id] = new_route

    return Solution(routes=routes, unassigned_orders=unassigned)


def improve_with_or_opt(
    solution: Solution,
    orders: list[Order],
    drivers: list[Driver],
    dm: DistanceMatrix,
    max_passes: int = 20,
) -> Solution:
    """
    Relocate single order pairs (pickup+dropoff moved together) to
    cheaper positions -- within the same route or across drivers -- until
    no improving move is found. Keeps pickup-before-dropoff and capacity
    valid at all times.
    """
    from backend.pdp.mode_solver import refine, distance
    refined = refine(solution, orders, drivers, dm, mode="save",
        economics={"activation_cost": 0.0, "cost_per_km": 1.0},
        timing={"speed_kph": 30.0, "service_minutes_per_stop": 0.0},
        metres_per_unit=1000.0, max_iterations=max(1, max_passes * max(1, len(orders))))
    for driver in drivers:
        refined.routes[driver.driver_id].total_distance = distance(refined.routes[driver.driver_id], driver, dm)
    return refined


def solve(orders: list[Order], drivers: list[Driver], dm: DistanceMatrix) -> Solution:
    solution = build_initial_solution(orders, drivers, dm)
    solution = improve_with_or_opt(solution, orders, drivers, dm)
    return solution
