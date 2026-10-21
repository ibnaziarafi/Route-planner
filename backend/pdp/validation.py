"""Independent audit of a PDP solution against original inputs and matrix."""
from math import isfinite
from backend.pdp.models import StopType, Route
from backend.pdp.mode_solver import metrics_for, distance


def validate(solution, orders, drivers, dm, *, mode="save", economics=None,
             timing=None, metres_per_unit=1000.0):
    errors = []
    order_ids = [o.order_id for o in orders]
    driver_ids = [d.driver_id for d in drivers]
    if len(order_ids) != len(set(order_ids)): errors.append("duplicate input order IDs")
    if len(driver_ids) != len(set(driver_ids)): errors.append("duplicate input driver IDs")
    if set(solution.routes) - set(driver_ids): errors.append("route references unknown driver")
    by_order = {o.order_id: o for o in orders}
    seen = {}
    for d in drivers:
        route = solution.routes.get(d.driver_id, Route(d.driver_id))
        load = 0
        for idx, stop in enumerate(route.stops):
            order = by_order.get(stop.order_id)
            if order is None:
                errors.append(f"unknown order {stop.order_id} in route"); continue
            expected = order.pickup_node if stop.stop_type == StopType.PICKUP else order.dropoff_node
            if stop.node != expected: errors.append(f"order {order.order_id} has wrong {stop.stop_type.value} node")
            if stop.stop_type not in (StopType.PICKUP, StopType.DROPOFF): errors.append("invalid stop type")
            load += order.demand if stop.stop_type == StopType.PICKUP else -order.demand
            if load < 0 or load > d.capacity: errors.append(f"driver {d.driver_id} load violates capacity/precedence")
            seen.setdefault(stop.order_id, []).append((d.driver_id, idx, stop.stop_type))
        if load != 0: errors.append(f"driver {d.driver_id} ends with nonzero load")
        if not isfinite(distance(route, d, dm)): errors.append(f"driver {d.driver_id} has unreachable/non-finite leg")
    unassigned = list(solution.unassigned_orders)
    if len(unassigned) != len(set(unassigned)): errors.append("duplicate unassigned order IDs")
    if set(unassigned) - set(order_ids): errors.append("unknown unassigned order")
    for oid in order_ids:
        pairs = seen.get(oid, [])
        if oid in unassigned:
            if pairs: errors.append(f"unassigned order {oid} is also served")
            continue
        if len(pairs) != 2 or sorted(p[2].value for p in pairs) != ["dropoff", "pickup"]:
            errors.append(f"order {oid} must have exactly one pickup and dropoff")
        else:
            pickup = next(pair for pair in pairs if pair[2] == StopType.PICKUP)
            dropoff = next(pair for pair in pairs if pair[2] == StopType.DROPOFF)
            if pickup[0] != dropoff[0]:
                errors.append(f"order {oid} pickup/dropoff use different drivers")
            elif pickup[1] >= dropoff[1]:
                errors.append(f"order {oid} pickup does not precede dropoff")
    served_or_unassigned = set(seen) | set(unassigned)
    if served_or_unassigned != set(order_ids): errors.append("order accounting is incomplete")
    m = metrics_for(solution, orders, drivers, dm, economics=economics, timing=timing,
                    metres_per_unit=metres_per_unit)
    complete = not unassigned and len(seen) == len(order_ids)
    if mode == "time" and set(d for d, r in solution.routes.items() if r.stops) != set(driver_ids):
        errors.append("Time mode requires every supplied driver to serve an order")
    return {"valid": not errors, "complete": complete, "errors": errors,
            "metrics": m, "objective_value": (m["economic_cost"] if mode == "save" else m["makespan_minutes"]) if not errors and complete else None}
