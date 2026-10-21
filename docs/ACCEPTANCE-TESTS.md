# Independent acceptance checks

This suite exercises the working application under `app/`, including its
backend API. It does not import the read-only `snapshot/` tree or use the
production benchmark evaluator as its sole reference. A small independent
enumerator assigns up to three orders across drivers and checks legal stop
orders to provide exact objective lower bounds.

`backend/tests/test_independent_acceptance.py` covers:

- Save fleet selection under different activation and per-kilometre rates.
- Installed OR-Tools and PyVRP Save and Time adapters, including complete
  feasible results, rate-driven fleet choice, all-driver activity, the
  makespan tradeoff, and checks against common fallback labels.
- Time's all-driver requirement, including a case that accepts more total
  distance for a lower makespan, heterogeneous capacities, and drivers
  outnumbering orders.
- Unreachable delivery legs, co-located zero-distance stops, and strict
  pickup-before-dropoff ordering.
- The frozen six-order duplicate-service fixture against live application
  modules, plus a direct validator rejection of duplicate service.
- Frozen learned-artifact inference, deterministic repeat output, feasibility,
  and controlled failure when the artifact is missing.
- Compare, model, and report API responses with strict JSON serialization.

Run from the application root:

```sh
.venv/bin/python -m pytest -q backend/tests/test_independent_acceptance.py
```

## Integration result — 20 October 2026

Ran from the `app/` root at base commit
`8fec97ac4570600f585ec9bfe229f80c9dd66412`. The checkout was dirty and
uncommitted. The tested backend and artifact tree, including the acceptance
test, had SHA-256 `2ad1d54e83c3f1d5e1c4c6653d5d25aa8ad4d3fe562f80189371956f56351d6c`
(72 files under `backend/` and `artifacts/`, excluding Python and pytest
caches). The acceptance test file itself had SHA-256
`3b322c37ec1292384b97c5d1a9f5f792debed52c9771bd33bf9cd3a33541a1ed`.

Command:

```sh
.venv/bin/python -m pytest -q backend/tests/test_independent_acceptance.py backend/tests/test_modes_backend.py backend/tests/test_learned_policy.py backend/tests/test_benchmark_api.py
```

Result: **26 passed** in 5.34 seconds. Four dependency deprecation warnings
were emitted: Starlette's `TestClient` import recommends `httpx2`, and
SWIG-generated types omit `__module__`. No test failed. The focused native
checks exercised installed OR-Tools and PyVRP adapters on both economic fleet
selection and the Time makespan case; they required valid complete results and
rejected a common fallback label. During integration, the independent checks
also exposed non-finite refinement scoring and native Time assignment issues;
the backend owner repaired those before this passing run.

The broader backend suite, frontend production build/browser journeys, and
held-out benchmark report were not run by this acceptance suite. API report
serialization is checked, but this suite does not claim benchmark performance
or general solver quality. The report endpoint may say `not_run` until the
explicit frozen evaluation is completed.

## Full backend integration run — 20 October 2026

After a subsequent backend integration update, the entire backend test suite
was run from the same dirty app checkout at base commit
`8fec97ac4570600f585ec9bfe229f80c9dd66412`:

```sh
.venv/bin/python -m pytest -q backend/tests
```

Result: **85 passed** in 7.12 seconds, with the same four dependency
deprecation warnings and no failures. At that run the backend and artifact tree
had SHA-256 `a3aff5a05fa0ed8b53e2444c43e7613babddfb7aeb7c2a1bda9de5448c683ba8`
(73 files, excluding Python and pytest caches). The acceptance test hash
remained `3b322c37ec1292384b97c5d1a9f5f792debed52c9771bd33bf9cd3a33541a1ed`.
