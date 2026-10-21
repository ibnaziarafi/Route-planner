"""Explicit CPU training: python -m backend.ml.train. Never called by the API."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import time

import numpy as np

from backend.ml.instances import SPLITS, instance, objective
from backend.ml.policy import ARTIFACT_PATH, FEATURE_NAMES, FEATURE_VERSION, rollout


def validation(weights, mode):
    scores = []
    for seed in SPLITS["validation"]:
        drivers, orders, dm, economics, timing, _ = instance(seed)
        solution, _ = rollout(orders, drivers, dm, weights, mode=mode, economics=economics,
                              timing=timing, time_limit_seconds=10)
        scores.append(objective(solution, drivers, orders, dm, mode, economics, timing))
    return float(np.mean(scores))


def main():
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {"splits": SPLITS, "generator": "backend.ml.instances.instance",
                "protocol": "500 episodes per mode; validation at 0/100/250/500; minimum mean normalized objective selects checkpoint; no test access in trainer",
                "limitation": "Same fixed 20-node topology across splits; seed separation is not unseen geography."}
    (ARTIFACT_PATH.parent / "split_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    start = time.perf_counter()
    curves, selected, selection = {}, {}, {}
    for mode_index, mode in enumerate(("save", "time")):
        rng = np.random.default_rng(6000 + mode_index)
        weights = np.zeros(14)
        moment = np.zeros(14)
        variance = np.zeros(14)
        baseline = None
        best = validation(weights, mode)
        selected[mode] = weights.copy()
        selection[mode] = {"episode": 0, "validation_score": best}
        curve = [{"episode": 0, "validation_score": best}]
        rewards = []
        for step, seed in enumerate(SPLITS["train"], 1):
            drivers, orders, dm, economics, timing, _ = instance(seed)
            solution, gradient = rollout(orders, drivers, dm, weights, mode=mode, economics=economics,
                                         timing=timing, time_limit_seconds=30, rng=rng, sample=True)
            reward = -objective(solution, drivers, orders, dm, mode, economics, timing)
            previous_baseline = reward if baseline is None else baseline
            baseline = reward if baseline is None else .95 * baseline + .05 * reward
            advantage = np.clip(reward - previous_baseline, -10, 10)
            g = np.clip(advantage * gradient, -5, 5)
            moment = .9 * moment + .1 * g
            variance = .999 * variance + .001 * g * g
            weights += .05 * (moment / (1 - .9 ** step)) / (np.sqrt(variance / (1 - .999 ** step)) + 1e-8)
            rewards.append(reward)
            if step % 50 == 0:
                row = {"episode": step, "mean_training_reward_last50": float(np.mean(rewards[-50:])),
                       "weight_l2": float(np.linalg.norm(weights))}
                if step in (100, 250, 500):
                    score = validation(weights, mode)
                    row["validation_score"] = score
                    if score < best:
                        best = score
                        selected[mode] = weights.copy()
                        selection[mode] = {"episode": step, "validation_score": score}
                curve.append(row)
                print(mode, row, flush=True)
        # A selected untrained baseline is not silently renamed a trained policy.
        if selection[mode]["episode"] == 0:
            selected[mode] = weights.copy()
            selection[mode] = {"episode": 500, "validation_score": validation(weights, mode),
                               "warning": "No trained checkpoint beat initialization on validation; final trained policy retained and limitation disclosed."}
        curves[mode] = curve
    source_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in [*Path(__file__).parent.glob("*.py"), Path(__file__).parents[1] / "pdp" / "mode_solver.py", Path(__file__).parents[1] / "graph" / "graph_data.py"]}
    metadata = {"algorithm": "Episodic REINFORCE with train-only exponential running baseline and Adam ascent",
                "architecture": "14-feature linear softmax insertion policy; separate Save/Time weights",
                "episodes_per_mode": 500, "total_episodes": 1000,
                "optimizer": {"name": "Adam", "learning_rate": .05, "beta1": .9, "beta2": .999,
                              "gradient_clip": 5, "advantage_clip": 10},
                "training_rng_seeds": [6000, 6001], "reward": "negative canonical objective /100 Save or /60 Time; 100 penalty per unserved order or idle Time driver",
                "selection": selection, "splits": SPLITS, "elapsed_seconds": time.perf_counter() - start,
                "python": platform.python_version(), "numpy": np.__version__, "source_hashes": source_hashes,
                "limitations": [manifest["limitation"], "Small synthetic training distribution, not a neural attention model or traffic predictor.",
                                "Deterministic order sequencing and hand-engineered features; only feasible insertion selection is learned.",
                                "No superiority or optimality guarantee; training time is separate from inference."]}
    data = {"feature_version": FEATURE_VERSION, "feature_names": FEATURE_NAMES,
            "weights": {mode: vector.tolist() for mode, vector in selected.items()}, "metadata": metadata}
    ARTIFACT_PATH.write_text(json.dumps(data, indent=2) + "\n")
    (ARTIFACT_PATH.parent / "learning_curve.json").write_text(json.dumps(curves, indent=2) + "\n")
    digest = hashlib.sha256(ARTIFACT_PATH.read_bytes()).hexdigest()
    (ARTIFACT_PATH.parent / "policy.sha256").write_text(f"{digest}  policy.json\n")
    print(json.dumps({"artifact": str(ARTIFACT_PATH), "sha256": digest,
                      "elapsed_seconds": metadata["elapsed_seconds"], "selection": selection}), flush=True)


if __name__ == "__main__":
    main()
