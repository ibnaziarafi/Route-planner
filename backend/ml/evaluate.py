"""One explicit held-out experiment. Refuses overwriting an inspected report.

Run python -m backend.ml.evaluate after freezing training. Native solvers run
at their declared one-second budgets; inference/training costs are distinct.
"""
from __future__ import annotations

from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import platform
import statistics
import subprocess
import time
from importlib.metadata import version

import numpy as np

from backend.ml.instances import SPLITS, instance, request_for_seed
from backend.ml.policy import ARTIFACT_PATH, model_metadata, rollout


def exact_objective(drivers, orders, dm, mode, economics, timing):
    """Independent enumeration of <=3 orders: assignments and stop permutations."""
    if len(orders) > 3:
        return None
    best = math.inf
    for assignments in itertools.product(range(len(drivers)), repeat=len(orders)):
        if mode == "time" and set(assignments) != set(range(len(drivers))):
            continue
        distances, lengths, possible = [], [], True
        for driver_index, driver in enumerate(drivers):
            assigned = [o for o, index in zip(orders, assignments) if index == driver_index]
            stops = [(o.order_id, kind, o.pickup_node if kind == "pickup" else o.dropoff_node, o.demand)
                     for o in assigned for kind in ("pickup", "dropoff")]
            shortest = math.inf
            for sequence in itertools.permutations(stops):
                node, distance, load = driver.start_node, 0., 0
                picked = set()
                valid = True
                for oid, kind, target, demand in sequence:
                    if kind == "dropoff" and oid not in picked:
                        valid = False
                        break
                    load += demand if kind == "pickup" else -demand
                    if not 0 <= load <= driver.capacity:
                        valid = False
                        break
                    if kind == "pickup":
                        picked.add(oid)
                    distance += dm.cost(node, target)
                    node = target
                if valid and load == 0:
                    shortest = min(shortest, distance)
            if not math.isfinite(shortest):
                possible = False
                break
            distances.append(shortest)
            lengths.append(len(stops))
        if not possible:
            continue
        if mode == "save":
            value = sum(bool(n) for n in lengths) * economics["activation_cost"] + sum(distances) * economics["cost_per_km"]
        else:
            value = max((d / timing["speed_kph"] * 60 + n * timing["service_minutes_per_stop"] for d, n in zip(distances, lengths)), default=0.)
        best = min(best, value)
    return best if math.isfinite(best) else None


def source_hash():
    digest = hashlib.sha256()
    for p in sorted(Path(__file__).parents[1].rglob("*.py")):
        digest.update(str(p.relative_to(Path(__file__).parents[1])).encode())
        digest.update(p.read_bytes())
    return digest.hexdigest()


def aggregates(cases):
    groups = defaultdict(list)
    for case in cases:
        for result in case["results"]:
            groups[case["mode"], result["method"]].append(result)
    rows = []
    for (mode, method), results in sorted(groups.items()):
        feasible = [r for r in results if r["status"] == "feasible" and r["validation"]["valid"]]
        objectives = [r["objective_value"] for r in feasible]
        times = [r["timings"]["solve_ms"] for r in feasible]
        rows.append({"mode": mode, "method": method, "method_label": results[0]["method_label"],
                     "cases": len(results), "feasible": len(feasible), "feasible_rate": len(feasible) / len(results),
                     "mean_objective": statistics.mean(objectives) if objectives else None,
                     "median_objective": statistics.median(objectives) if objectives else None,
                     "median_solve_ms": statistics.median(times) if times else None,
                     "p95_solve_ms": float(np.percentile(times, 95)) if times else None})
    return rows


def main():
    from backend.benchmarks.router import CompareRequest, compare
    from backend.pdp.validation import validate
    out = ARTIFACT_PATH.parent / "benchmark_report.json"
    if out.exists():
        raise SystemExit("Report exists. Preserve the test evidence; do not overwrite or tune on these test seeds.")
    started = time.perf_counter()
    cases = []
    for mode in ("save", "time"):
        for seed in SPLITS["test"]:
            request = request_for_seed(seed, mode)
            response = compare(CompareRequest(**request))
            drivers, orders, dm, economics, timing, profile = instance(seed)
            oracle = exact_objective(drivers, orders, dm, mode, economics, timing)
            # Identical feasible insertion environment, no trained weights.
            before = time.perf_counter()
            solution, _ = rollout(orders, drivers, dm, np.zeros(14), mode=mode,
                                  economics=economics, timing=timing, time_limit_seconds=1)
            ablation_ms = (time.perf_counter() - before) * 1000
            audit = validate(solution, orders, drivers, dm, mode=mode, economics=economics,
                             timing=timing, metres_per_unit=1000)
            feasible = audit["valid"] and audit["complete"]
            response["results"].append({"method": "untrained", "method_label": "Zero-weight insertion policy (ablation)",
                                         "status": "feasible" if feasible else "invalid",
                                         "objective_value": audit["objective_value"] if feasible else None,
                                         "metrics": audit["metrics"], "validation": audit,
                                         "timings": {"solve_ms": ablation_ms}, "routes": solution.as_dict()["routes"]})
            case = {"instance_seed": seed, "mode": mode, "scenario": profile,
                    "request": request, "request_id": response["request_id"], "matrix_ms": response["matrix_ms"],
                    "exact_optimum": oracle, "reference_type": "exact_enumeration" if oracle is not None else "best_known_feasible",
                    "results": response["results"]}
            valid_scores = [r["objective_value"] for r in case["results"] if r["status"] == "feasible"]
            reference = oracle if oracle is not None else min(valid_scores, default=None)
            case["reference_objective"] = reference
            for result in case["results"]:
                if result["status"] == "feasible" and reference is not None:
                    result["reference_absolute_gap"] = result["objective_value"] - reference
                    result["reference_gap_percent"] = (result["objective_value"] / reference - 1) * 100 if reference else None
            cases.append(case)
            print(mode, seed, [(r["method"], r["status"], r["objective_value"]) for r in case["results"]], flush=True)
    # Library randomness measured on a declared common subset, kept apart
    # from the main equal-instance aggregates (no duplicate weighting).
    stochastic = []
    for mode in ("save", "time"):
        for solver_seed in (0, 1, 2, 3, 4):
            request = request_for_seed(3000, mode, methods=["pyvrp"])
            request["seed"] = solver_seed
            response = compare(CompareRequest(**request))
            stochastic.append({"instance_seed": 3000, "mode": mode, "solver_seed": solver_seed,
                               "results": response["results"]})
    metadata = {"model": model_metadata(), "source_tree_sha256": source_hash(),
                "upstream_base": "8fec97ac4570600f585ec9bfe229f80c9dd66412",
                "platform": platform.platform(), "python": platform.python_version(),
                "versions": {p: version(p) for p in ("numpy", "ortools", "pyvrp", "networkx", "fastapi")},
                "splits": SPLITS, "budget_seconds": 1, "elapsed_seconds": time.perf_counter() - started,
                "test_case_count": len(cases), "main_method_runs": sum(len(c["results"]) for c in cases),
                "protocol": "Frozen trained checkpoint; 12 held-out instance seeds per mode; one-second native budgets; zero-policy ablation; 5 PyVRP seeds on instance3000 in each mode; no test-based retraining"}
    report = {"status": "complete", "metadata": metadata, "aggregates": aggregates(cases), "cases": cases,
              "stochastic_subset": stochastic,
              "limitations": ["Small synthetic 20-node topology; held-out instance seeds do not establish unseen-city or real-world generalization.",
                              "Objective averages mix different rates and workload sizes; use paired per-case gaps for method comparisons.",
                              "Feasible-only objective means report their denominators; failures never win.",
                              "Native solvers have one-second search budgets; learned policy and scratch may finish earlier; training cost is separate.",
                              "Five-seed variability experiment covers one instance per mode, not the whole distribution.",
                              "Time values are assumptions-based estimates with simultaneous starts, not live traffic ETA.",
                              "PyVRP Time is a named hybrid, not a native minimax algorithm."]}
    out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": str(out), "aggregates": report["aggregates"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
