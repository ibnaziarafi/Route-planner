# Experiment findings — 20 October 2026

The frozen local RL policy was evaluated once on 12 held-out instance seeds in each mode (24 cases, 120 main method results including the untrained ablation). A separate five-seed PyVRP subset uses one fixed instance per mode. There are four tiny cases with independently enumerated optima; larger references are best-known feasible values, not proven optima. Raw evidence is in `artifacts/learned/benchmark_report.json`.

| Mode | Method | Complete feasible | Median objective | Median solve ms |
| --- | --- | --- | --- | --- |
| save | learned | 12/12 | 166.00 | 0.480 |
| save | ortools | 12/12 | 141.50 | 1000.566 |
| save | pyvrp | 9/12 | 144.00 | 704.569 |
| save | scratch | 12/12 | 161.50 | 1.625 |
| save | untrained | 12/12 | 224.00 | 0.477 |
| time | learned | 12/12 | 71.50 | 0.464 |
| time | ortools | 12/12 | 65.00 | 1000.112 |
| time | pyvrp | 12/12 | 69.00 | 706.988 |
| time | scratch | 12/12 | 65.00 | 5.988 |
| time | untrained | 12/12 | 159.50 | 0.243 |

Save objective is generic economic cost; Time objective is final parallel completion in assumed minutes. Cases vary in workload, economics and timing, so use paired per-case comparisons before aggregate objective medians. Feasibility denominators differ for PyVRP Save; its feasible-only median must not hide failures.

The learned policy improved over zero-weight inference in all 12 Save cases and 11/12 Time cases. It beat the custom heuristic in one Time case, but generally lost to classical search. Against OR-Tools it had 10 losses/2 ties in Save and 9 losses/3 ties in Time. Mean paired relative objective differences versus OR-Tools were +12.67% Save and +6.58% Time (higher is worse). Against zero weights, mean paired differences were -27.70% Save and -37.42% Time. These are observed results on this small declared dataset, not general accuracy or speedup claims.

PyVRP Save returned no feasible incumbent in seeds 3002, 3008 and 3011 under the declared budget split. The library emitted a PenaltyBoundWarning about difficulty finding feasibility and possible scale differences. Preserve these failures. Investigating economic scaling or search settings is future development and requires a fresh held-out manifest after tuning; the current report has not been replaced. All Time methods and all other Save rows were complete and valid. The zero-weight baseline is deliberately untrained, not a strong competing heuristic; the custom solver is the stronger deterministic baseline.

Native methods receive a one-second overall search allowance; PyVRP reserves a fraction for shared refinement and reports actual phase/model metadata. Custom and learned construction may finish earlier. ML median inference here is below 1 ms, but its solution quality is usually worse. The final training run took approximately 0.42 seconds for 1000 tiny episodes; timing is local to this work host. Several fixed-seed software-integration training runs were discarded before the final freeze, including a provisional environment-mask defect. There was no model tuning or retraining after inspecting the held-out report. Final checkpoint selection used validation only.

Training and held-out generators vary fleet size independently of geography profile. Both use the same small 20-node topology and unit-demand orders; this is not evidence for unseen cities, high demand magnitudes, many orders or realistic traffic. Feature engineering and deterministic order sequencing are part of the environment. The policy is a 28-coefficient linear softmax RL baseline, not a deep attention architecture. There is no hidden refinement in its principal row.

Final runtime validation: 87 backend tests pass with four dependency deprecation warnings. This includes independent acceptance, native Save fleet-rate and Time-makespan regressions, duplicate service, per-order precedence and distance-cache repairs, and learned artifact tests. Frontend production build and whitespace checks pass. `docs/ACCEPTANCE-TESTS.md` retains the independent engineer's earlier 85-test run; manager then added/verified the two lead-found regression repairs in the 87-test integration run. Browser evidence is recorded in `docs/BROWSER-QA.md`.

Docker context was adjusted to include the frozen learned artifacts and cached graph and exclude the local virtual environment. No Docker daemon build, Azure deployment, production privacy/security audit, assistive-technology audit or unseen-geography benchmark was performed. The legacy backend-context Vercel Dockerfile is not the supported packaging path for the new artifact; use the root-context backend/Dockerfile if building a container. Local startup is reproducible through run-local.command.

The feature is ready as a conditional portfolio experiment with explicit failure cases and limitations. It does not establish operational navigation accuracy, globally shortest completion, market demand or learning outcomes.
