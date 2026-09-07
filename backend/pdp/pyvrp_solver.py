"""PyVRP implementation of the multi-driver pickup-and-delivery solver."""

from pyvrp import Model
from pyvrp._pyvrp import ActivityType
from pyvrp.stop import MaxRuntime

from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType


def solve(
    orders: list[Order],
    drivers: list[Driver],
    dm: DistanceMatrix,
    max_runtime_seconds: float = 5.0,
    seed: int = 0,
) -> Solution:
    """Solve open multi-vehicle PDP with PyVRP's hybrid genetic search."""
    routes = {driver.driver_id: Route(driver_id=driver.driver_id) for driver in drivers}
    if not orders:
        return Solution(routes=routes)

    model = Model()
    location_of = {
        node: model.add_location(x=0, y=0, name=node)
        for node in dm.nodes
    }
    virtual_end = model.add_location(x=0, y=0, name="__virtual_end__")
    shared_end_depot = model.add_depot(virtual_end)

    for driver in drivers:
        start_depot = model.add_depot(location_of[driver.start_node])
        model.add_vehicle_type(
            num_available=1,
            capacity=driver.capacity,
            start_depot=start_depot,
            end_depot=shared_end_depot,
            name=f"driver-{driver.driver_id}",
        )

    for source in dm.nodes:
        for target in dm.nodes:
            if source != target:
                distance = dm.cost(source, target)
                model.add_edge(
                    location_of[source],
                    location_of[target],
                    distance=int(round(distance)) if distance != float("inf") else 10**9,
                )
        model.add_edge(location_of[source], virtual_end, distance=0)

    shipments = []
    for order in orders:
        shipment = model.add_shipment(
            location_of[order.pickup_node],
            location_of[order.dropoff_node],
            amount=order.demand,
            name=f"order-{order.order_id}",
        )
        shipments.append((shipment, order))

    result = model.solve(
        stop=MaxRuntime(max_runtime_seconds),
        seed=seed,
        display=False,
    )
    if result.best is None:
        return Solution(
            routes=routes,
            unassigned_orders=[order.order_id for order in orders],
        )

    driver_ids = [driver.driver_id for driver in drivers]
    assigned_order_ids = set()
    for pyvrp_route in result.best.routes():
        driver_id = driver_ids[pyvrp_route.vehicle_type()]
        route = routes[driver_id]
        for activity in pyvrp_route:
            if activity.type == ActivityType.DEPOT:
                continue
            _, order = shipments[activity.idx]
            if activity.type == ActivityType.PICKUP:
                route.stops.append(
                    Stop(order.order_id, order.pickup_node, StopType.PICKUP)
                )
            elif activity.type == ActivityType.DELIVERY:
                route.stops.append(
                    Stop(order.order_id, order.dropoff_node, StopType.DROPOFF)
                )
                assigned_order_ids.add(order.order_id)
        route.total_distance = pyvrp_route.distance()

    return Solution(
        routes=routes,
        unassigned_orders=[
            order.order_id
            for order in orders
            if order.order_id not in assigned_order_ids
        ],
    )