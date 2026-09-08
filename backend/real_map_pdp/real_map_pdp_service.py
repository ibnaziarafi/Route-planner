"""Coordinate adapter around the existing PDP solvers and route algorithms."""

from backend.algorithms.astar import astar
from backend.algorithms.dijkstra import dijkstra
from backend.algorithms.dijkstra_v2 import dijkstra_v2
from backend.pdp.models import Driver, Order
from backend.pdp.ortools_solver import solve as solve_ortools
from backend.pdp.pyvrp_solver import solve as solve_pyvrp
from backend.pdp.scratch_solver import solve as solve_scratch
from backend.real_map.osm_graph import get_hobart_adapter
from backend.real_map_pdp.real_map_distance_matrix import RealMapDistanceMatrix


def _route_algorithm(algorithm, graph, start, end):
    if algorithm == "dijkstra":
        return dijkstra(graph, start, end)
    if algorithm == "dijkstra_v2":
        return dijkstra_v2(graph, start, end)
    if algorithm == "a_star":
        return astar(graph, start, end, graph.positions)
    raise ValueError("Unsupported shortest-path algorithm.")


def solve_real_map_pdp(request, graph=None) -> dict:
    graph = graph or get_hobart_adapter()
    locations = []
    drivers = []
    for driver_request in request.drivers:
        node = graph.nearest_node(driver_request.start_lat, driver_request.start_lon)
        if node is None:
            raise ValueError("A driver location is outside the available Hobart road map.")
        drivers.append(Driver(driver_request.driver_id, node, driver_request.capacity))
        locations.append(node)

    orders = []
    for order_request in request.orders:
        pickup = graph.nearest_node(order_request.pickup_lat, order_request.pickup_lon)
        dropoff = graph.nearest_node(order_request.dropoff_lat, order_request.dropoff_lon)
        if pickup is None or dropoff is None:
            raise ValueError(f"Order {order_request.order_id} is outside the available Hobart road map.")
        orders.append(Order(order_request.order_id, pickup, dropoff, order_request.demand))
        locations.extend((pickup, dropoff))

    if len({driver.driver_id for driver in drivers}) != len(drivers):
        raise ValueError("Driver IDs must be unique.")
    if len({order.order_id for order in orders}) != len(orders):
        raise ValueError("Order IDs must be unique.")

    relevant_nodes = sorted(set(locations))
    matrix = RealMapDistanceMatrix(relevant_nodes, graph)
    if request.solver == "scratch":
        solution = solve_scratch(orders, drivers, matrix)
    elif request.solver == "ortools":
        solution = solve_ortools(orders, drivers, matrix, request.time_limit_seconds)
    elif request.solver == "pyvrp":
        solution = solve_pyvrp(orders, drivers, matrix, request.time_limit_seconds)
    else:
        raise ValueError("Unsupported PDP solver.")

    driver_by_id = {driver.driver_id: driver for driver in drivers}
    routes = []
    for driver_id, route in solution.routes.items():
        driver = driver_by_id[driver_id]
        full_path = []
        detailed_stops = []
        current_node = driver.start_node
        full_path.append(current_node)
        for stop in route.stops:
            segment, segment_distance = _route_algorithm(
                request.algorithm, graph, current_node, stop.node
            )
            if not segment:
                raise ValueError(f"No road route between {current_node} and {stop.node}.")
            full_path.extend(segment[1:])
            position = graph.coordinates(stop.node)
            detailed_stops.append({
                "order_id": stop.order_id,
                "node": stop.node,
                "type": stop.stop_type.value,
                "lat": position["lat"],
                "lon": position["lon"],
            })
            current_node = stop.node

        routes.append({
            "driver_id": driver_id,
            "capacity": driver.capacity,
            "total_distance_km": round(route.total_distance / 1000, 3),
            "stops": detailed_stops,
            "full_path": [
                {"node": node, "lat": graph.coordinates(node)["lat"], "lon": graph.coordinates(node)["lon"]}
                for node in full_path
            ],
        })

    route_nodes = {
        point["node"]
        for route in routes
        for point in route["full_path"]
    }
    positions = {
        node: {"lat": graph.coordinates(node)["lat"], "lon": graph.coordinates(node)["lon"]}
        for node in route_nodes
    }
    return {
        "algorithm": request.algorithm,
        "solver": request.solver,
        "total_distance_km": round(solution.total_distance / 1000, 3),
        "routes": routes,
        "unassigned_orders": solution.unassigned_orders,
        "positions": positions,
    }
