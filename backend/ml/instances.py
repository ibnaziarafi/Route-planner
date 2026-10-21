"""Frozen synthetic experiment generator, split by seed, not by geography."""
from __future__ import annotations

import random

from backend.graph.graph_data import get_graph_and_positions
from backend.pdp.distance_matrix import DistanceMatrix
from backend.pdp.models import Driver, Order

SPLITS = {"train": list(range(1000, 1500)), "validation": list(range(2000, 2012)),
          "test": list(range(3000, 3012))}


def instance(seed):
    rng = random.Random(seed)
    graph, _ = get_graph_and_positions("medium")
    nodes = graph.get_nodes()
    profile = ("clustered", "dispersed", "remote")[seed % 3]
    pool = nodes[:10] if profile == "clustered" else nodes
    # Fleet size must vary independently of the geography profile; coupling
    # both to seed % 3 would confound the scenario comparison.
    n_drivers = rng.randint(1, 3)
    n_orders = rng.randint(max(3, n_drivers), 6)
    drivers = [Driver(i + 1, rng.choice(nodes), rng.randint(1, 3)) for i in range(n_drivers)]
    orders = [Order(i + 1, rng.choice(pool), rng.choice(pool), 1) for i in range(n_orders)]
    if profile == "remote":
        orders[-1] = Order(n_orders, nodes[-1], nodes[-2], 1)
    economics = {"activation_cost": rng.choice([2., 10., 30.]), "cost_per_km": rng.choice([.5, 2., 5.])}
    timing = {"speed_kph": rng.choice([20., 30., 45.]), "service_minutes_per_stop": rng.choice([.5, 1., 2.])}
    relevant = sorted({d.start_node for d in drivers} | {n for o in orders for n in (o.pickup_node, o.dropoff_node)})
    dm = DistanceMatrix(relevant, graph)
    return drivers, orders, dm, economics, timing, profile


def request_for_seed(seed, mode, methods=None, budget=1):
    drivers, orders, _, economics, timing, profile = instance(seed)
    return {"dataset": "synthetic", "graph_type": "medium", "scenario": profile,
            "mode": mode, "seed": seed, "methods": methods or ["scratch", "ortools", "pyvrp", "learned"],
            "time_limit_seconds": budget, "metres_per_unit": 1000,
            "economics": economics, "timing": timing,
            "drivers": [vars(d) for d in drivers], "orders": [vars(o) for o in orders]}


def objective(solution, drivers, orders, dm, mode, economics, timing, metres_per_unit=1000):
    """Training reward evaluator; final product has a separate independent audit."""
    total = 0.
    makespan = 0.
    active = 0
    observed = []
    for driver in drivers:
        route = solution.routes[driver.driver_id]
        if not route.stops:
            continue
        active += 1
        node = driver.start_node
        distance = 0.
        for stop in route.stops:
            distance += dm.cost(node, stop.node)
            node = stop.node
            observed.append((stop.order_id, stop.stop_type.value))
        km = distance * metres_per_unit / 1000
        total += km
        makespan = max(makespan, km / timing["speed_kph"] * 60 + len(route.stops) * timing["service_minutes_per_stop"])
    cost = active * economics["activation_cost"] + total * economics["cost_per_km"]
    penalty = len(solution.unassigned_orders) * 100
    if mode == "time":
        penalty += (len(drivers) - active) * 100
    value = cost if mode == "save" else makespan
    return value / (100 if mode == "save" else 60) + penalty
