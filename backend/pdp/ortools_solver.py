"""OR-Tools implementation of the multi-driver pickup-and-delivery solver."""

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType


def solve(
    orders: list[Order],
    drivers: list[Driver],
    dm: DistanceMatrix,
    time_limit_seconds: int = 5,
) -> Solution:
    """Solve open multi-vehicle PDP with capacity and precedence constraints."""
    routes = {driver.driver_id: Route(driver_id=driver.driver_id) for driver in drivers}
    if not orders:
        return Solution(routes=routes)

    locations = [driver.start_node for driver in drivers]
    pickup_index_of = {}
    dropoff_index_of = {}
    for order in orders:
        pickup_index_of[order.order_id] = len(locations)
        locations.append(order.pickup_node)
        dropoff_index_of[order.order_id] = len(locations)
        locations.append(order.dropoff_node)

    dummy_end = len(locations)
    manager = pywrapcp.RoutingIndexManager(
        len(locations) + 1,
        len(drivers),
        list(range(len(drivers))),
        [dummy_end] * len(drivers),
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        if from_node == dummy_end or to_node == dummy_end:
            return 0
        distance = dm.cost(locations[from_node], locations[to_node])
        return int(round(distance * 1000)) if distance != float("inf") else 10**12

    transit_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)
    routing.AddDimension(transit_index, 0, 10**12, True, "Distance")
    distance_dimension = routing.GetDimensionOrDie("Distance")

    demands = [0] * (len(locations) + 1)
    for order in orders:
        demands[pickup_index_of[order.order_id]] = order.demand
        demands[dropoff_index_of[order.order_id]] = -order.demand

    def demand_callback(index):
        return demands[manager.IndexToNode(index)]

    demand_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_index,
        0,
        [driver.capacity for driver in drivers],
        True,
        "Capacity",
    )

    for order in orders:
        pickup = manager.NodeToIndex(pickup_index_of[order.order_id])
        dropoff = manager.NodeToIndex(dropoff_index_of[order.order_id])
        routing.AddPickupAndDelivery(pickup, dropoff)
        routing.solver().Add(routing.VehicleVar(pickup) == routing.VehicleVar(dropoff))
        routing.solver().Add(
            distance_dimension.CumulVar(pickup)
            <= distance_dimension.CumulVar(dropoff)
        )

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_parameters.time_limit.FromSeconds(time_limit_seconds)

    assignment = routing.SolveWithParameters(search_parameters)
    if assignment is None:
        return Solution(routes=routes, unassigned_orders=[order.order_id for order in orders])

    pickup_orders = {index: order_id for order_id, index in pickup_index_of.items()}
    dropoff_orders = {index: order_id for order_id, index in dropoff_index_of.items()}
    for vehicle_id, driver in enumerate(drivers):
        index = routing.Start(vehicle_id)
        route = routes[driver.driver_id]
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node in pickup_orders:
                route.stops.append(
                    Stop(pickup_orders[node], locations[node], StopType.PICKUP)
                )
            elif node in dropoff_orders:
                route.stops.append(
                    Stop(dropoff_orders[node], locations[node], StopType.DROPOFF)
                )
            index = assignment.Value(routing.NextVar(index))
        route.total_distance = (
            assignment.Value(distance_dimension.CumulVar(routing.End(vehicle_id))) / 1000
        )

    return Solution(routes=routes)