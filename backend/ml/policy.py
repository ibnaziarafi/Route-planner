"""Feasibility-masked linear policy trained with episodic REINFORCE.

The model selects a driver and a pickup/delivery insertion. It does not
predict traffic, replace the road graph, or run local search after inference.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

from backend.pdp.models import Route, Solution

ARTIFACT_PATH = Path(__file__).resolve().parents[2] / "artifacts" / "learned" / "policy.json"
FEATURE_VERSION = "insertion-14-v1"
FEATURE_NAMES = ["bias", "delta_km_100", "route_km_100", "fleet_km_100",
                 "economic_cost_1000", "driver_minutes_240", "makespan_minutes_240",
                 "newly_active", "active_fraction", "capacity_fraction",
                 "route_stop_fraction", "remaining_fraction", "activation_1000", "per_km_10"]


def model_metadata():
    if not ARTIFACT_PATH.exists():
        return {"available": False, "status": "not_trained", "reason": "Run python -m backend.ml.train explicitly."}
    try:
        data = json.loads(ARTIFACT_PATH.read_text())
        _check_artifact(data)
    except (ValueError, KeyError, TypeError, OSError) as error:
        return {"available": False, "status": "invalid_artifact", "reason": str(error)}
    curve_path = ARTIFACT_PATH.parent / "learning_curve.json"
    curves = json.loads(curve_path.read_text()) if curve_path.exists() else {}
    return {**data.get("metadata", {}), "available": True, "status": "trained", "learning_curve": curves,
            "feature_version": FEATURE_VERSION, "features": FEATURE_NAMES,
            "parameter_count": 28, "sha256": hashlib.sha256(ARTIFACT_PATH.read_bytes()).hexdigest(),
            "method_label": "Locally trained linear RL insertion policy"}


def _check_artifact(data):
    if data["feature_version"] != FEATURE_VERSION:
        raise ValueError("Unsupported learned feature version")
    for mode in ("save", "time"):
        vector = np.asarray(data["weights"][mode], dtype=float)
        if vector.shape != (14,) or not np.all(np.isfinite(vector)):
            raise ValueError("Learned weights must contain 14 finite numbers per mode")


def model_status():
    """Public read-only API metadata; loading never trains or mutates weights."""
    return model_metadata()


def load_weights(mode):
    if mode not in ("save", "time"):
        raise ValueError("Unsupported optimization mode")
    if not ARTIFACT_PATH.exists():
        raise RuntimeError("Learned model is unavailable: run its explicit training command first.")
    data = json.loads(ARTIFACT_PATH.read_text())
    _check_artifact(data)
    return np.asarray(data["weights"][mode], dtype=float)


def feature_matrix(candidates, order, orders, drivers, remaining_orders, economics, metres_per_unit):
    by_id = {d.driver_id: d for d in drivers}
    n_orders = max(1, len(orders))
    km = metres_per_unit / 1000
    rows = []
    for c in candidates:
        rows.append([1, c["distance_delta"] * km / 100,
                     c["route_distance"] * km / 100, c["total_distance"] * km / 100,
                     c["economic_cost"] / 1000, c["completion_minutes"] / 240,
                     c["makespan_minutes"] / 240, float(c["newly_active"]),
                     c["active_drivers"] / max(1, len(drivers)),
                     order.demand / by_id[c["driver_id"]].capacity,
                     len(c["route"].stops) / (2 * n_orders),
                     len(remaining_orders) / n_orders, economics["activation_cost"] / 1000,
                     economics["cost_per_km"] / 10])
    return np.clip(np.asarray(rows, dtype=float), -10, 10)


def rollout(orders, drivers, dm, weights, *, mode="save", economics=None, timing=None,
            metres_per_unit=1000.0, time_limit_seconds=5.0, rng=None, sample=False):
    from backend.pdp.mode_solver import feasible_insertions
    economics = {"activation_cost": 20., "cost_per_km": .5, **(economics or {})}
    timing = {"speed_kph": 30., "service_minutes_per_stop": 1., **(timing or {})}
    solution = Solution(routes={d.driver_id: Route(d.driver_id) for d in drivers})
    ordered = sorted(orders, key=lambda o: (min((dm.cost(d.start_node, o.pickup_node)
                                                for d in drivers), default=math.inf), o.order_id))
    gradient = np.zeros(14)
    deadline = time.monotonic() + time_limit_seconds
    for index, order in enumerate(ordered):
        if time.monotonic() >= deadline:
            solution.unassigned_orders.extend(o.order_id for o in ordered[index:])
            break
        remaining = ordered[index:]
        candidates = feasible_insertions(solution, order, orders, drivers, dm,
                                         mode=mode, economics=economics, timing=timing,
                                         metres_per_unit=metres_per_unit, remaining_orders=remaining, deadline=deadline)
        if not candidates:
            solution.unassigned_orders.append(order.order_id)
            continue
        x = feature_matrix(candidates, order, orders, drivers, remaining, economics, metres_per_unit)
        logits = x @ weights
        probabilities = np.exp(logits - logits.max())
        probabilities /= probabilities.sum()
        selected = int(rng.choice(len(candidates), p=probabilities)) if sample else int(np.argmax(logits))
        gradient += x[selected] - probabilities @ x
        candidate = candidates[selected]
        solution.routes[candidate["driver_id"]] = candidate["route"]
    return solution, gradient


def solve(orders, drivers, dm, *, mode="save", economics=None, timing=None,
          metres_per_unit=1000.0, time_limit_seconds=5.0, seed=0):
    """Frozen deterministic inference; seed recorded for API parity only."""
    solution, _ = rollout(orders, drivers, dm, load_weights(mode), mode=mode,
                          economics=economics, timing=timing, metres_per_unit=metres_per_unit,
                          time_limit_seconds=time_limit_seconds)
    solution.metadata.update({"termination": "policy_completed" if not solution.unassigned_orders else "policy_incomplete",
                              "refinement": "none", "seed_effect": "Frozen deterministic argmax; seed does not change inference"})
    return solution
