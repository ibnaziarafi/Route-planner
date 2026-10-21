"""PyVRP implementation of the multi-driver pickup-and-delivery solver."""

from pyvrp import Model
from pyvrp.stop import MaxRuntime
import time
from math import isfinite

from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType
from backend.pdp.mode_solver import solve_mode, refine, feasible_insertions, distance as canonical_distance


def _activity_name(activity) -> str:
    """Read activity names across PyVRP versions without private imports."""
    activity_type = getattr(activity, "type", None)
    return getattr(activity_type, "name", str(activity_type).split(".")[-1]).upper()


def solve(
    orders: list[Order],
    drivers: list[Driver],
    dm: DistanceMatrix,
    max_runtime_seconds: float = 5.0,
    seed: int = 0,
    *, mode: str = "save", economics=None, timing=None, metres_per_unit: float = 1000.0,
) -> Solution:
    """Solve open multi-vehicle PDP with PyVRP's hybrid genetic search."""
    started=time.monotonic(); deadline=started+float(max_runtime_seconds)
    economics, timing = economics or {}, timing or {}
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
            fixed_cost=int(round(economics.get("activation_cost",20)*1_000_000)) if mode=="save" else 0,
            unit_distance_cost=1,
            name=f"driver-{driver.driver_id}",
        )

    for source in dm.nodes:
        for target in dm.nodes:
            if source != target:
                distance = dm.cost(source, target)
                if not isfinite(distance): continue
                if mode == "save":
                    edge_cost=distance*metres_per_unit/1000*economics.get("cost_per_km",.5)*1_000_000
                else:
                    edge_cost=distance*metres_per_unit
                model.add_edge(location_of[source], location_of[target], distance=max(0,int(round(edge_cost))))
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

    native_budget=max(.001,min(float(max_runtime_seconds)*.7,deadline-time.monotonic()))
    result = model.solve(
        stop=MaxRuntime(native_budget),
        seed=seed,
        display=False,
    )
    native_feasible = result.best is not None and result.best.is_feasible()
    if not native_feasible:
        if mode == "time":
            fallback, termination=solve_mode(orders,drivers,dm,mode="time",economics=economics,
                timing=timing,metres_per_unit=metres_per_unit,deadline=deadline)
            fallback.metadata.update({"adapter":"PyVRP seed unavailable; common Time construction used",
                                     "termination":termination,"native_seed_feasible":False})
            return fallback
        return Solution(routes=routes,unassigned_orders=[order.order_id for order in orders],
                        metadata={"native_seed_feasible":False})

    driver_ids = [driver.driver_id for driver in drivers]
    assigned_order_ids = set()
    for pyvrp_route in result.best.routes():
        driver_id = driver_ids[pyvrp_route.vehicle_type()]
        route = routes[driver_id]
        for activity in pyvrp_route:
            activity_name = _activity_name(activity)
            if activity_name == "DEPOT":
                continue
            _, order = shipments[activity.idx]
            if activity_name == "PICKUP":
                route.stops.append(
                    Stop(order.order_id, order.pickup_node, StopType.PICKUP)
                )
            elif activity_name in {"DELIVERY", "DROPOFF"}:
                route.stops.append(
                    Stop(order.order_id, order.dropoff_node, StopType.DROPOFF)
                )
                assigned_order_ids.add(order.order_id)
        route.total_distance = canonical_distance(route, drivers[driver_ids.index(driver_id)], dm)

    native_solution = Solution(
        routes=routes,
        unassigned_orders=[
            order.order_id
            for order in orders
            if order.order_id not in assigned_order_ids
        ],
    )
    if mode == "time":
        # PyVRP's public objective is distance based. Use its result only as a
        # seed when it already activates every driver; otherwise search a
        # contract-valid incumbent with the common Time algorithm.
        # Repair native idle vehicles by moving complete order pairs from a
        # donor that retains another order. Each insertion is checked by the
        # common directed-matrix and capacity feasibility mask.
        repaired = True
        while any(not native_solution.routes[d.driver_id].stops for d in drivers) and repaired and time.monotonic() < deadline:
            repaired = False
            idle = next((d for d in drivers if not native_solution.routes[d.driver_id].stops), None)
            for donor in drivers:
                donor_route=native_solution.routes[donor.driver_id]
                order_ids=list(dict.fromkeys(s.order_id for s in donor_route.stops))
                if len(order_ids)<2: continue
                for oid in order_ids:
                    order=next(o for o in orders if o.order_id==oid)
                    stripped=Route(donor.driver_id,[s for s in donor_route.stops if s.order_id!=oid])
                    trial_routes=dict(native_solution.routes); trial_routes[donor.driver_id]=stripped
                    trial=Solution(trial_routes, list(native_solution.unassigned_orders))
                    options=feasible_insertions(trial,order,orders,drivers,dm,mode="time",
                        economics=economics,timing=timing,metres_per_unit=metres_per_unit,
                        remaining_orders=[order],deadline=deadline)
                    options=[option for option in options if option["driver_id"]==idle.driver_id]
                    if options:
                        selected=min(options,key=lambda option:(option["makespan_minutes"],option["total_distance"]))
                        trial.routes[idle.driver_id]=selected["route"]
                        native_solution=trial; repaired=True; break
                if repaired: break
        if not native_solution.unassigned_orders and all(native_solution.routes[d.driver_id].stops for d in drivers):
            refined=refine(native_solution, orders, drivers, dm, mode="time", economics=economics,
                          timing=timing, metres_per_unit=metres_per_unit, deadline=deadline)
            refined.metadata.update({"adapter":"PyVRP distance seed + all-driver repair + Time refinement","native_seed_feasible":True,"seed_objective":result.best.distance(),"native_budget_seconds":native_budget})
            return refined
        fallback, termination = solve_mode(orders, drivers, dm, mode="time", economics=economics,
            timing=timing, metres_per_unit=metres_per_unit, deadline=deadline,seed=seed)
        fallback.metadata.update({"adapter":"PyVRP distance seed discarded; common Time construction + refinement","native_seed_feasible":True,"termination":termination,"seed_objective":result.best.distance()})
        return fallback
    refined=refine(native_solution, orders, drivers, dm, mode="save", economics=economics,
                  timing=timing, metres_per_unit=metres_per_unit, deadline=deadline)
    refined.metadata.update({"adapter":"PyVRP economic seed + common economic refinement","native_seed_feasible":True,"seed_objective":result.best.distance(),"native_budget_seconds":native_budget})
    return refined
