"""Independent acceptance checks for the Route Planner benchmark milestone.

These exercise the live app modules and API. The tiny oracle below enumerates
assignments and legal pickup/dropoff permutations independently of the
production evaluator.
"""
from collections import Counter
from itertools import permutations, product
import json
import math

from fastapi.testclient import TestClient

from backend.main import app
from backend.pdp.models import Driver, Order, Route, Solution, Stop, StopType
from backend.pdp.mode_solver import metrics_for, solve_mode
from backend.pdp.validation import validate


class Matrix:
    def __init__(self, costs):
        self.costs = costs
        self.nodes = sorted({node for edge in costs for node in edge})

    def cost(self, source, target):
        if source == target:
            return 0.0
        return self.costs.get((source, target), math.inf)


def _independent_optimum(orders, drivers, dm, *, mode, economics, timing,
                         metres_per_unit=1000.0):
    """Enumerate all order assignments and legal stop orders for <=3 orders."""
    assert len(orders) <= 3
    best = math.inf
    for assignment in product(range(len(drivers)), repeat=len(orders)):
        if mode == "time" and set(assignment) != set(range(len(drivers))):
            continue
        distances, durations, active = [], [], 0
        possible = True
        for driver_index, driver in enumerate(drivers):
            assigned = [o for o, index in zip(orders, assignment)
                        if index == driver_index]
            if assigned:
                active += 1
            activities = [(o.order_id, kind,
                           o.pickup_node if kind == "pickup" else o.dropoff_node,
                           o.demand)
                          for o in assigned for kind in ("pickup", "dropoff")]
            shortest = math.inf
            for sequence in permutations(activities):
                node, distance, load, picked = driver.start_node, 0.0, 0, set()
                valid = True
                for order_id, kind, target, demand in sequence:
                    if kind == "dropoff" and order_id not in picked:
                        valid = False
                        break
                    load += demand if kind == "pickup" else -demand
                    if not 0 <= load <= driver.capacity:
                        valid = False
                        break
                    if kind == "pickup":
                        picked.add(order_id)
                    leg = dm.cost(node, target)
                    if not math.isfinite(leg):
                        valid = False
                        break
                    distance += leg
                    node = target
                if valid and load == 0:
                    shortest = min(shortest, distance)
            if not math.isfinite(shortest):
                possible = False
                break
            distances.append(shortest)
            duration = (shortest * metres_per_unit / 1000 /
                        timing["speed_kph"] * 60 +
                        len(activities) * timing["service_minutes_per_stop"])
            durations.append(duration)
        if not possible:
            continue
        value = (active * economics["activation_cost"] +
                 sum(distances) * metres_per_unit / 1000 * economics["cost_per_km"]
                 if mode == "save" else max(durations, default=0.0))
        best = min(best, value)
    return None if not math.isfinite(best) else best


def _served_pairs(solution):
    return Counter((stop.order_id, stop.stop_type.value)
                   for route in solution.routes.values() for stop in route.stops)


def test_save_activation_rate_changes_fleet_and_matches_tiny_oracle():
    dm = Matrix({
        ("S1", "P1"): 1, ("P1", "D1"): 1, ("D1", "P2"): 10,
        ("P2", "D2"): 2, ("S2", "P2"): 1, ("S1", "P2"): 50,
        ("D2", "P1"): 10, ("S2", "P1"): 15, ("D1", "P2"): 10,
    })
    drivers = [Driver(1, "S1", 2), Driver(2, "S2", 2)]
    orders = [Order(1, "P1", "D1"), Order(2, "P2", "D2")]
    timing = {"speed_kph": 60, "service_minutes_per_stop": 0}
    cheap_activation = {"activation_cost": 0, "cost_per_km": 1}
    expensive_activation = {"activation_cost": 20, "cost_per_km": 0}

    economical, _ = solve_mode(orders, drivers, dm, mode="save",
        economics=cheap_activation, timing=timing, time_limit_seconds=1)
    compact_fleet, _ = solve_mode(orders, drivers, dm, mode="save",
        economics=expensive_activation, timing=timing, time_limit_seconds=1)

    assert sum(bool(r.stops) for r in economical.routes.values()) == 2
    assert sum(bool(r.stops) for r in compact_fleet.routes.values()) == 1
    for solution, economics in ((economical, cheap_activation),
                                (compact_fleet, expensive_activation)):
        audit = validate(solution, orders, drivers, dm, mode="save",
                         economics=economics, timing=timing)
        optimum = _independent_optimum(orders, drivers, dm, mode="save",
                                       economics=economics, timing=timing)
        assert audit["valid"] and audit["complete"]
        assert audit["objective_value"] >= optimum


def test_time_uses_every_driver_and_trades_distance_for_lower_makespan():
    dm = Matrix({("S1", "P1"): 1, ("P1", "D1"): 1,
                 ("D1", "P2"): 10, ("P2", "D2"): 2,
                 ("S2", "P2"): 11, ("D2", "P1"): 10,
                 ("S2", "P1"): 15, ("D1", "P2"): 10})
    drivers = [Driver(1, "S1", 2), Driver(2, "S2", 2)]
    orders = [Order(1, "P1", "D1"), Order(2, "P2", "D2")]
    timing = {"speed_kph": 60, "service_minutes_per_stop": 0}
    time_solution, _ = solve_mode(orders, drivers, dm, mode="time", timing=timing,
                                  time_limit_seconds=1)
    sequential, _ = solve_mode(orders, [drivers[0]], dm, mode="save",
        economics={"activation_cost": 0, "cost_per_km": 1}, timing=timing,
        time_limit_seconds=1)
    time_audit = validate(time_solution, orders, drivers, dm, mode="time", timing=timing)
    sequential_metrics = metrics_for(sequential, orders, [drivers[0]], dm, timing=timing)

    assert time_audit["valid"] and time_audit["complete"]
    assert time_audit["metrics"]["active_drivers"] == len(drivers)
    assert time_audit["metrics"]["total_distance"] > sequential_metrics["total_distance"]
    assert time_audit["metrics"]["makespan_minutes"] < sequential_metrics["makespan_minutes"]
    optimum = _independent_optimum(orders, drivers, dm, mode="time",
                                   economics={}, timing=timing)
    assert time_audit["objective_value"] >= optimum


def test_time_capacity_matching_handles_heterogeneous_drivers_and_count_failure():
    dm = Matrix({("S1", "P1"): 1, ("P1", "D1"): 1,
                 ("S1", "P2"): 2, ("P2", "D2"): 1,
                 ("S2", "P1"): 2, ("S2", "P2"): 1,
                 ("D1", "P2"): 1, ("D2", "P1"): 1})
    drivers = [Driver(1, "S1", 1), Driver(2, "S2", 3)]
    orders = [Order(1, "P1", "D1", 2), Order(2, "P2", "D2", 1)]
    solution, reason = solve_mode(orders, drivers, dm, mode="time", time_limit_seconds=1)
    audit = validate(solution, orders, drivers, dm, mode="time")
    assert reason in {"local_optimum", "time_limit"}
    assert audit["valid"] and audit["complete"]
    assert solution.routes[1].stops[0].order_id == 2
    assert solution.routes[2].stops[0].order_id == 1

    too_many, reason = solve_mode(orders, [*drivers, Driver(3, "S1", 3)],
                                  dm, mode="time", time_limit_seconds=1)
    assert reason == "drivers_exceed_orders"
    assert too_many.unassigned_orders == [o.order_id for o in orders]


def test_native_adapters_solve_save_rates_and_time_makespan_cases():
    from backend.pdp.ortools_solver import solve as solve_ortools
    from backend.pdp.pyvrp_solver import solve as solve_pyvrp

    adapters = {
        "ortools": lambda orders, drivers, dm, mode, economics, timing:
            solve_ortools(orders, drivers, dm, 1, mode=mode,
                          economics=economics, timing=timing),
        "pyvrp": lambda orders, drivers, dm, mode, economics, timing:
            solve_pyvrp(orders, drivers, dm, 1, seed=0, mode=mode,
                        economics=economics, timing=timing),
    }
    save_matrix = Matrix({("S1", "P1"): 1, ("P1", "D1"): 1,
                          ("D1", "P2"): 10, ("P2", "D2"): 2,
                          ("S2", "P2"): 1, ("S1", "P2"): 50,
                          ("D2", "P1"): 10, ("S2", "P1"): 15})
    drivers = [Driver(1, "S1", 2), Driver(2, "S2", 2)]
    orders = [Order(1, "P1", "D1"), Order(2, "P2", "D2")]
    for name, solve in adapters.items():
        low_activation = solve(orders, drivers, save_matrix, "save",
                               {"activation_cost": 0, "cost_per_km": 1}, {})
        high_activation = solve(orders, drivers, save_matrix, "save",
                                {"activation_cost": 20, "cost_per_km": 0}, {})
        for solution in (low_activation, high_activation):
            audit = validate(solution, orders, drivers, save_matrix, mode="save")
            assert audit["valid"] and audit["complete"], (name, audit)
            assert "fallback" not in str(solution.metadata.get("adapter", "")).lower()
        assert sum(bool(r.stops) for r in low_activation.routes.values()) == 2, name
        assert sum(bool(r.stops) for r in high_activation.routes.values()) == 1, name

    time_matrix = Matrix({("S1", "P1"): 1, ("P1", "D1"): 1,
                          ("D1", "P2"): 10, ("P2", "D2"): 2,
                          ("S2", "P2"): 11, ("D2", "P1"): 10,
                          ("S2", "P1"): 15, ("S1", "P2"): 50,
                          ("P1", "P2"): 10, ("P2", "P1"): 10,
                          ("D1", "P1"): 0, ("D2", "P2"): 0})
    timing = {"speed_kph": 60, "service_minutes_per_stop": 0}
    sequential, _ = solve_mode(orders, [drivers[0]], time_matrix, mode="save",
        economics={"activation_cost": 0, "cost_per_km": 1}, timing=timing,
        time_limit_seconds=1)
    sequential_metrics = metrics_for(sequential, orders, [drivers[0]], time_matrix,
                                     timing=timing)
    optimum = _independent_optimum(orders, drivers, time_matrix, mode="time",
                                   economics={}, timing=timing)
    for name, solve in adapters.items():
        solution = solve(orders, drivers, time_matrix, "time", {}, timing)
        audit = validate(solution, orders, drivers, time_matrix, mode="time", timing=timing)
        assert audit["valid"] and audit["complete"], (name, audit)
        assert audit["metrics"]["active_drivers"] == len(drivers), name
        assert audit["metrics"]["total_distance"] > sequential_metrics["total_distance"], name
        assert audit["metrics"]["makespan_minutes"] < sequential_metrics["makespan_minutes"], name
        assert audit["objective_value"] >= optimum, name
        adapter_label = solution.metadata.get("adapter", "")
        assert "fallback" not in adapter_label.lower(), (name, adapter_label)
        if name == "pyvrp":
            assert solution.metadata.get("native_seed_feasible") is True


def test_unreachable_order_is_unassigned_and_zero_length_stops_keep_precedence():
    blocked = Matrix({("S", "P"): 1})
    driver, order = Driver(1, "S", 1), Order(1, "P", "D")
    partial, _ = solve_mode([order], [driver], blocked, mode="save", time_limit_seconds=1)
    assert partial.unassigned_orders == [1]
    assert not validate(partial, [order], [driver], blocked)["complete"]

    colocated = Matrix({})
    zero_driver, zero_order = Driver(1, "X", 1), Order(1, "X", "X")
    zero, _ = solve_mode([zero_order], [zero_driver], colocated,
                         mode="save", time_limit_seconds=1)
    stops = zero.routes[1].stops
    assert [s.stop_type for s in stops] == [StopType.PICKUP, StopType.DROPOFF]
    audit = validate(zero, [zero_order], [zero_driver], colocated)
    assert audit["valid"] and audit["complete"]


def test_validator_rejects_frozen_duplicate_service_and_solver_repairs_fixture():
    costs = [
        [0,17,19,24,28,12,15,15,31,10], [15,0,17,14,12,9,5,18,14,25],
        [13,2,0,13,9,11,7,1,16,10], [6,17,25,0,29,18,9,17,23,15],
        [32,38,36,36,0,28,41,24,28,41], [21,10,8,21,17,0,15,9,24,18],
        [15,26,34,9,29,27,0,26,29,24], [12,15,13,12,22,23,17,0,24,22],
        [17,20,18,26,9,25,21,19,0,16], [20,15,13,14,22,9,5,14,29,0],
    ]
    dm = Matrix({(str(i), str(j)): costs[i][j]
                 for i in range(10) for j in range(10)})
    drivers = [Driver(1, "0", 2), Driver(2, "1", 2)]
    orders = [Order(i, p, d) for i, p, d in [
        (1, "7", "6"), (2, "0", "6"), (3, "0", "3"),
        (4, "2", "7"), (5, "7", "4"), (6, "2", "6")]]
    duplicated = Solution({1: Route(1, [
        Stop(1, "7", StopType.PICKUP), Stop(1, "6", StopType.DROPOFF),
        Stop(1, "7", StopType.PICKUP), Stop(1, "6", StopType.DROPOFF)])}, [])
    bad_audit = validate(duplicated, [orders[0]], [drivers[0]], dm)
    assert not bad_audit["valid"]
    assert any("exactly one" in error for error in bad_audit["errors"])

    repaired, _ = solve_mode(orders, drivers, dm, mode="save",
                             economics={"activation_cost": 0, "cost_per_km": 1},
                             time_limit_seconds=1)
    expected = Counter((o.order_id, kind) for o in orders
                       for kind in ("pickup", "dropoff"))
    assert _served_pairs(repaired) == expected
    repair_audit = validate(repaired, orders, drivers, dm, mode="save",
                            economics={"activation_cost": 0, "cost_per_km": 1})
    assert repair_audit["valid"] and repair_audit["complete"]


def test_learned_artifact_is_frozen_deterministic_and_never_falls_back(monkeypatch, tmp_path):
    from backend.ml import policy
    from backend.ml.instances import instance

    metadata = policy.model_metadata()
    assert metadata["available"] is True
    assert metadata["method_label"] == "Locally trained linear RL insertion policy"
    drivers, orders, dm, economics, timing, _ = instance(2001)
    first = policy.solve(orders, drivers, dm, mode="save", economics=economics,
                         timing=timing, time_limit_seconds=2)
    second = policy.solve(orders, drivers, dm, mode="save", economics=economics,
                          timing=timing, time_limit_seconds=2)
    assert first.as_dict() == second.as_dict()
    audit = validate(first, orders, drivers, dm, mode="save",
                     economics=economics, timing=timing)
    assert audit["valid"] and audit["complete"]
    assert _served_pairs(first) == Counter((o.order_id, kind) for o in orders
                                            for kind in ("pickup", "dropoff"))

    monkeypatch.setattr(policy, "ARTIFACT_PATH", tmp_path / "missing-policy.json")
    assert policy.model_metadata()["available"] is False
    try:
        policy.solve(orders, drivers, dm, mode="save", economics=economics,
                     timing=timing, time_limit_seconds=2)
    except RuntimeError as error:
        assert "unavailable" in str(error).lower()
    else:
        raise AssertionError("missing artifact silently returned a fallback solution")


def test_compare_model_and_report_responses_are_serializable_and_honest():
    client = TestClient(app)
    payload = {
        "dataset": "synthetic", "graph_type": "small", "mode": "save",
        "methods": ["scratch"], "time_limit_seconds": 1,
        "drivers": [{"driver_id": 1, "start_node": "A", "capacity": 2}],
        "orders": [{"order_id": 1, "pickup_node": "B", "dropoff_node": "F", "demand": 1}],
    }
    comparison = client.post("/api/benchmarks/compare", json=payload)
    assert comparison.status_code == 200
    result = comparison.json()
    json.dumps(result, allow_nan=False)
    row = result["results"][0]
    assert row["status"] == "feasible"
    assert row["validation"]["valid"] and row["objective_value"] is not None

    model_response = client.get("/api/benchmarks/model")
    report_response = client.get("/api/benchmarks/report")
    assert model_response.status_code == report_response.status_code == 200
    model, report = model_response.json(), report_response.json()
    json.dumps(model, allow_nan=False)
    json.dumps(report, allow_nan=False)
    assert model.get("available") is True or model.get("status") == "unavailable"
    assert report.get("status") in {"not_run", "complete"}
