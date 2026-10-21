"""Canonical mode objectives and immutable feasible insertion candidates."""
from copy import deepcopy
from math import isfinite
import time

from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType


def distance(route, driver, dm):
    nodes = [driver.start_node] + [s.node for s in route.stops]
    values = [dm.cost(a, b) for a, b in zip(nodes, nodes[1:])]
    return sum(values) if all(isfinite(x) for x in values) else float("inf")


def objective(metrics, mode):
    return metrics["economic_cost"] if mode == "save" else metrics["makespan_minutes"]


def metrics_for(solution, orders, drivers, dm, *, economics=None, timing=None,
                metres_per_unit=1000.0):
    economics, timing = economics or {}, timing or {}
    by_driver = {d.driver_id: d for d in drivers}
    distances = [distance(solution.routes.get(d.driver_id, Route(d.driver_id)), d, dm) for d in drivers]
    if not all(isfinite(value) for value in distances):
        return {"total_distance": None, "total_distance_km": None, "economic_cost": None,
                "makespan_minutes": None,
                "active_drivers": sum(bool(solution.routes.get(d.driver_id) and solution.routes[d.driver_id].stops) for d in drivers),
                "served_orders": len(orders) - len(solution.unassigned_orders), "total_orders": len(orders),
                "completion_by_driver": {d.driver_id: None for d in drivers}}
    total = sum(distances)
    active = sum(bool(solution.routes.get(d.driver_id) and solution.routes[d.driver_id].stops) for d in drivers)
    km = total * metres_per_unit / 1000
    rate = economics.get("cost_per_km", .5)
    activation = economics.get("activation_cost", 20)
    durations = [distances[i] * metres_per_unit / 1000 / timing.get("speed_kph", 30) * 60 + len(solution.routes.get(d.driver_id, Route(d.driver_id)).stops) * timing.get("service_minutes_per_stop", 1) for i, d in enumerate(drivers)]
    return {"total_distance": total, "total_distance_km": km,
            "economic_cost": activation * active + rate * km,
            "makespan_minutes": max(durations, default=0), "active_drivers": active,
            "served_orders": len(orders) - len(solution.unassigned_orders), "total_orders": len(orders),
            "completion_by_driver": {d.driver_id: durations[i] for i, d in enumerate(drivers)}}


def _capacity_ok(stops, capacity, by_order):
    load = 0
    for stop in stops:
        order = by_order.get(stop.order_id)
        if order is None: return False
        load += order.demand if stop.stop_type == StopType.PICKUP else -order.demand
        if load < 0 or load > capacity: return False
    return load == 0


def feasible_insertions(solution, order, orders, drivers, dm, *, mode, economics,
                        timing, metres_per_unit, remaining_orders, deadline=None):
    """Enumerate immutable legal insertions in deterministic driver/pair order."""
    by_order = {o.order_id: o for o in orders}
    if order.order_id in {s.order_id for r in solution.routes.values() for s in r.stops}:
        return []
    existing_active = {did for did, route in solution.routes.items() if route.stops}
    unused = {d.driver_id for d in drivers} - existing_active
    candidates = []
    for driver in sorted(drivers, key=lambda d: d.driver_id):
        if deadline is not None and time.monotonic() >= deadline: return candidates
        if mode == "time" and driver.driver_id in existing_active and len(remaining_orders) == len(unused):
            continue
        if order.demand > driver.capacity: continue
        route = solution.routes.get(driver.driver_id, Route(driver.driver_id))
        n = len(route.stops)
        for pi in range(n + 1):
            if deadline is not None and time.monotonic() >= deadline: return candidates
            for di in range(pi + 1, n + 2):
                if deadline is not None and time.monotonic() >= deadline: return candidates
                stops = list(route.stops)
                stops.insert(pi, Stop(order.order_id, order.pickup_node, StopType.PICKUP))
                stops.insert(di, Stop(order.order_id, order.dropoff_node, StopType.DROPOFF))
                if not _capacity_ok(stops, driver.capacity, by_order): continue
                replacement = Route(driver.driver_id, stops)
                rd = distance(replacement, driver, dm)
                if not isfinite(rd): continue
                replacement.total_distance = rd
                newroutes = dict(solution.routes); newroutes[driver.driver_id] = replacement
                trial = Solution(newroutes, list(solution.unassigned_orders))
                m = metrics_for(trial, orders, drivers, dm, economics=economics,
                                timing=timing, metres_per_unit=metres_per_unit)
                if m["economic_cost"] is None or m["makespan_minutes"] is None: continue
                oldd = distance(route, driver, dm)
                candidates.append({"route": replacement, "driver_id": driver.driver_id,
                    "pickup_index": pi, "dropoff_index": di, "distance_delta": rd-oldd,
                    "route_distance": rd, "total_distance": m["total_distance"],
                    "economic_cost": m["economic_cost"],
                    "completion_minutes": m["completion_by_driver"][driver.driver_id],
                    "makespan_minutes": m["makespan_minutes"], "active_drivers": m["active_drivers"],
                    "newly_active": driver.driver_id not in existing_active})
    return candidates


def solve_mode(orders, drivers, dm, *, mode="save", economics=None, timing=None,
               metres_per_unit=1000.0, time_limit_seconds=2.0, seed=0, deadline=None):
    """Build an objective-aware feasible incumbent and refine within a deadline."""
    import time
    deadline = deadline or (time.monotonic() + max(.001, float(time_limit_seconds)))
    solution = Solution({d.driver_id: Route(d.driver_id) for d in drivers}, [])
    pending = list(orders)
    if mode == "time" and len(drivers) > len(orders):
        solution.unassigned_orders = [o.order_id for o in orders]
        return solution, "drivers_exceed_orders"
    # Find a distinct feasible seed order per driver. This establishes active
    # routes without claiming that the remaining orders are globally assignable.
    if mode == "time":
        order_owner = {}
        def assign(driver, visited):
            if time.monotonic() >= deadline: return False
            for candidate in pending:
                if candidate.order_id in visited or candidate.demand > driver.capacity: continue
                if not (isfinite(dm.cost(driver.start_node, candidate.pickup_node)) and
                        isfinite(dm.cost(candidate.pickup_node, candidate.dropoff_node))): continue
                visited.add(candidate.order_id)
                owner = order_owner.get(candidate.order_id)
                if owner is None or assign(owner, visited):
                    order_owner[candidate.order_id] = driver
                    return True
            return False
        matched = all(assign(driver, set()) for driver in sorted(drivers,key=lambda d:d.driver_id))
        if not matched or len(order_owner) < len(drivers):
            solution.unassigned_orders = [o.order_id for o in orders]
            return solution, "no_feasible_all_driver_seed"
        assignments = [(order_owner[o.order_id],o) for o in pending if o.order_id in order_owner]
        for d, o in assignments:
            route = Route(d.driver_id, [Stop(o.order_id, o.pickup_node, StopType.PICKUP),
                                        Stop(o.order_id, o.dropoff_node, StopType.DROPOFF)])
            route.total_distance = distance(route, d, dm)
            solution.routes[d.driver_id] = route
            pending = [x for x in pending if x.order_id != o.order_id]
    # Stable order processing also matches the policy feature protocol.
    def nearest(o):
        return min((dm.cost(d.start_node, o.pickup_node) for d in drivers), default=float("inf"))
    pending.sort(key=lambda o: (nearest(o), o.order_id))
    for index, order in enumerate(pending):
        if time.monotonic() >= deadline:
            solution.unassigned_orders.extend(o.order_id for o in pending[index:]); break
        remaining = pending[index:]
        options = feasible_insertions(solution, order, orders, drivers, dm, mode=mode,
            economics=economics, timing=timing, metres_per_unit=metres_per_unit,
            remaining_orders=remaining, deadline=deadline)
        if not options:
            solution.unassigned_orders.append(order.order_id); continue
        def score(c):
            return (c["economic_cost"] if mode == "save" else c["makespan_minutes"],
                    c["total_distance"], c["driver_id"], c["pickup_index"], c["dropoff_index"])
        selected = min(options, key=score)
        solution.routes[selected["driver_id"]] = selected["route"]
    solution = refine(solution, orders, drivers, dm, mode=mode, economics=economics,
                      timing=timing, metres_per_unit=metres_per_unit, deadline=deadline)
    return solution, "time_limit" if time.monotonic() >= deadline else "local_optimum"


def refine(solution, orders, drivers, dm, *, mode="save", economics=None, timing=None,
           metres_per_unit=1000, deadline=None, max_iterations=10_000):
    """Monotonic relocation (and Time pair swaps) with fresh ownership per move."""
    import time
    economics, timing = economics or {}, timing or {}
    best = deepcopy(solution)
    for _ in range(max_iterations):
        if deadline is not None and time.monotonic() >= deadline: break
        current = objective(metrics_for(best, orders, drivers, dm, economics=economics,
                                        timing=timing, metres_per_unit=metres_per_unit), mode)
        if current is None: return best
        accepted = None
        for did, route in list(best.routes.items()):
            ids = list(dict.fromkeys(s.order_id for s in route.stops))
            for oid in ids:
                if deadline is not None and time.monotonic() >= deadline: break
                driver = next(d for d in drivers if d.driver_id == did)
                stripped = Route(did, [s for s in route.stops if s.order_id != oid])
                routes = dict(best.routes); routes[did] = stripped
                trial = Solution(routes, list(best.unassigned_orders))
                # Time routes must remain active; relocating the final order is forbidden.
                if mode == "time" and not stripped.stops: continue
                order = next(o for o in orders if o.order_id == oid)
                options = feasible_insertions(trial, order, orders, drivers, dm, mode=mode,
                    economics=economics, timing=timing, metres_per_unit=metres_per_unit,
                    remaining_orders=[order], deadline=deadline)
                for option in options:
                    candidate_routes = dict(trial.routes); candidate_routes[option["driver_id"]] = option["route"]
                    candidate = Solution(candidate_routes, list(best.unassigned_orders))
                    value = objective(metrics_for(candidate, orders, drivers, dm, economics=economics,
                        timing=timing, metres_per_unit=metres_per_unit), mode)
                    if value is None: continue
                    if value < current - 1e-9:
                        accepted = candidate; break
                if accepted: break
            if accepted: break
        # A makespan search must be able to exchange the sole orders of two
        # active drivers. Single-order relocation cannot do that without
        # temporarily deactivating a driver, which the Time feasibility rule
        # correctly forbids. Build each exchange simultaneously, preserving
        # both active routes throughout the candidate evaluation.
        if accepted is None and mode == "time":
            by_driver = {d.driver_id: d for d in drivers}
            active_ids = [did for did, route in best.routes.items() if route.stops]
            by_order = {o.order_id: o for o in orders}
            for left_idx, left_id in enumerate(active_ids):
                left = best.routes[left_id]
                for right_id in active_ids[left_idx + 1:]:
                    if deadline is not None and time.monotonic() >= deadline: break
                    right = best.routes[right_id]
                    left_orders = list(dict.fromkeys(s.order_id for s in left.stops))
                    right_orders = list(dict.fromkeys(s.order_id for s in right.stops))
                    for left_order_id in left_orders:
                        if deadline is not None and time.monotonic() >= deadline: break
                        left_order = by_order[left_order_id]
                        for right_order_id in right_orders:
                            if deadline is not None and time.monotonic() >= deadline: break
                            right_order = by_order[right_order_id]
                            routes = dict(best.routes)
                            routes[left_id] = Route(left_id, [s for s in left.stops if s.order_id != left_order_id])
                            routes[right_id] = Route(right_id, [s for s in right.stops if s.order_id != right_order_id])
                            stripped = Solution(routes, list(best.unassigned_orders))
                            # Enumerate legal pickup/dropoff positions for the
                            # swapped orders, restricting each to its new driver.
                            first_options = feasible_insertions(stripped, right_order, orders, drivers, dm,
                                mode="save", economics=economics, timing=timing,
                                metres_per_unit=metres_per_unit, remaining_orders=[right_order], deadline=deadline)
                            for first in first_options:
                                if first["driver_id"] != left_id: continue
                                intermediate_routes = dict(stripped.routes)
                                intermediate_routes[left_id] = first["route"]
                                intermediate = Solution(intermediate_routes, list(best.unassigned_orders))
                                second_options = feasible_insertions(intermediate, left_order, orders, drivers, dm,
                                    mode="save", economics=economics, timing=timing,
                                    metres_per_unit=metres_per_unit, remaining_orders=[left_order], deadline=deadline)
                                for second in second_options:
                                    if second["driver_id"] != right_id: continue
                                    candidate_routes = dict(intermediate.routes)
                                    candidate_routes[right_id] = second["route"]
                                    candidate = Solution(candidate_routes, list(best.unassigned_orders))
                                    value = objective(metrics_for(candidate, orders, drivers, dm,
                                        economics=economics, timing=timing,
                                        metres_per_unit=metres_per_unit), mode)
                                    if value is not None and value < current - 1e-9:
                                        accepted = candidate
                                        break
                                if accepted: break
                            if accepted: break
                        if accepted: break
                    if accepted: break
                if accepted: break
        if accepted is None: break
        best = accepted
    # Refinement computes objectives from the matrix, independently of route
    # caches. Refresh every returned route so legacy PDP and real-map response
    # wrappers, which expose Route.total_distance, see the same final solution.
    for driver in drivers:
        route = best.routes.setdefault(driver.driver_id, Route(driver.driver_id))
        route.total_distance = distance(route, driver, dm)
    return best
