"""OR-Tools implementation of the multi-driver pickup-and-delivery solver."""

from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType


def solve(
    orders: list[Order],
    drivers: list[Driver],
    dm: DistanceMatrix,
    time_limit_seconds: int = 5,
    *, mode: str = "save", economics=None, timing=None, metres_per_unit: float = 1000.0,
) -> Solution:
    """Solve open multi-vehicle PDP with capacity and precedence constraints."""
    import time
    started = time.monotonic()
    deadline = started + float(time_limit_seconds)
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

    economics, timing = economics or {}, timing or {}
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        if from_node == dummy_end or to_node == dummy_end:
            return 0
        distance = dm.cost(locations[from_node], locations[to_node])
        return int(round(distance * 1000)) if distance != float("inf") else 10**12

    if mode == "save":
        scale = 1_000_000
        def cost_callback(i, j):
            raw = distance_callback(i, j) / 1000
            km = raw * metres_per_unit / 1000
            return int(round(km * economics.get("cost_per_km", .5) * scale))
        cost_index = routing.RegisterTransitCallback(cost_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(cost_index)
        fixed = int(round(economics.get("activation_cost", 20) * scale))
        for vehicle in range(len(drivers)): routing.SetFixedCostOfVehicle(fixed, vehicle)
        time_index = transit_index = routing.RegisterTransitCallback(distance_callback)
        routing.AddDimension(transit_index, 0, 10**12, True, "Distance")
        distance_dimension = routing.GetDimensionOrDie("Distance")
    elif mode == "time":
        speed = timing.get("speed_kph", 30)
        service_ms = int(round(timing.get("service_minutes_per_stop", 1) * 60_000))
        def duration_callback(i, j):
            source, target = manager.IndexToNode(i), manager.IndexToNode(j)
            if source == dummy_end or target == dummy_end: return 0
            travel = dm.cost(locations[source], locations[target])
            travel_ms = int(round(travel * metres_per_unit / 1000 / speed * 3_600_000)) if travel != float("inf") else 10**12
            return travel_ms + (service_ms if target >= len(drivers) else 0)
        duration_index = routing.RegisterTransitCallback(duration_callback)
        zero_index = routing.RegisterTransitCallback(lambda i, j: 0)
        routing.SetArcCostEvaluatorOfAllVehicles(zero_index)
        routing.AddDimension(duration_index, 0, 10**12, True, "Duration")
        duration_dimension = routing.GetDimensionOrDie("Duration")
        duration_dimension.SetGlobalSpanCostCoefficient(1)
        for vehicle in range(len(drivers)):
            routing.solver().Add(routing.NextVar(routing.Start(vehicle)) != routing.End(vehicle))
        # Keep a distance dimension for diagnostics/precedence.
        transit_index = routing.RegisterTransitCallback(distance_callback)
        routing.AddDimension(transit_index, 0, 10**12, True, "Distance")
        distance_dimension = routing.GetDimensionOrDie("Distance")
    else:
        raise ValueError("mode must be save or time")

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

    routing.AddDimension(routing.RegisterTransitCallback(lambda i, j: 1), 0, len(orders)*2+1, True, "Rank")
    rank_dimension = routing.GetDimensionOrDie("Rank")

    for order in orders:
        pickup = manager.NodeToIndex(pickup_index_of[order.order_id])
        dropoff = manager.NodeToIndex(dropoff_index_of[order.order_id])
        routing.AddPickupAndDelivery(pickup, dropoff)
        routing.solver().Add(routing.VehicleVar(pickup) == routing.VehicleVar(dropoff))
        routing.solver().Add(rank_dimension.CumulVar(pickup) < rank_dimension.CumulVar(dropoff))

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    if mode == "time":
        # Build a common-feasible all-driver incumbent, then let OR-Tools
        # optimize its native global-span objective within the same deadline.
        from backend.pdp.mode_solver import solve_mode, metrics_for
        seed_deadline=min(deadline, started + max(.01, float(time_limit_seconds)*.15))
        seed_solution, _ = solve_mode(orders, drivers, dm, mode="time", economics=economics,
            timing=timing, metres_per_unit=metres_per_unit, deadline=seed_deadline)
        complete_seed=not seed_solution.unassigned_orders and all(seed_solution.routes[d.driver_id].stops for d in drivers)
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        search_parameters.time_limit.FromMilliseconds(max(1,int(max(0,deadline-time.monotonic())*1000)))
        routing.CloseModelWithParameters(search_parameters)
        assignment=None
        if complete_seed:
            route_nodes=[]
            for driver in drivers:
                node_route=[]
                for stop in seed_solution.routes[driver.driver_id].stops:
                    node_route.append(pickup_index_of[stop.order_id] if stop.stop_type == StopType.PICKUP else dropoff_index_of[stop.order_id])
                route_nodes.append(node_route)
            warm_start=routing.ReadAssignmentFromRoutes(route_nodes, False)
            if warm_start is not None and time.monotonic() < deadline:
                assignment=routing.SolveFromAssignmentWithParameters(warm_start,search_parameters)
        if assignment is None and time.monotonic() < deadline:
            assignment=routing.SolveWithParameters(search_parameters)
        if assignment is None and complete_seed:
            assignment=warm_start
    else:
        native_budget_ms = max(1, int(float(time_limit_seconds) * 1000))
        search_parameters.time_limit.FromMilliseconds(native_budget_ms)
        assignment = routing.SolveWithParameters(search_parameters)
    if assignment is None:
        if mode == "time":
            from backend.pdp.mode_solver import solve_mode
            fallback, termination = solve_mode(orders, drivers, dm, mode="time",
                economics=economics, timing=timing, metres_per_unit=metres_per_unit,
                deadline=deadline)
            fallback.metadata["adapter"] = "OR-Tools makespan search unavailable; common Time fallback"
            fallback.metadata["termination"] = termination
            return fallback
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
        route.total_distance = sum(dm.cost(a, b.node) for a,b in zip([driver.start_node]+[s.node for s in route.stops[:-1]], route.stops))

    metadata={}
    if mode == "time":
        metadata={"adapter":"OR-Tools makespan search + objective-aware warm start",
                  "native_objective":"global_duration_span","duration_quantization":"integer milliseconds",
                  "seed_used":False,"warm_start_objective":metrics_for(seed_solution,orders,drivers,dm,
                      economics=economics,timing=timing,metres_per_unit=metres_per_unit)["makespan_minutes"]}
    elif mode == "save":
        metadata={"native_objective":"economic arc cost + fixed active-vehicle cost",
                  "integer_currency_scale":1_000_000,"seed_used":False}
    return Solution(routes=routes,metadata=metadata)
