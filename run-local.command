#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# The Codex desktop bundle is an optional convenience on this work host.
if ! command -v node >/dev/null 2>&1 && [[ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" ]]; then
  export PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH"
fi
if command -v pnpm >/dev/null 2>&1; then
  ROUTE_PM=(pnpm)
elif [[ -x "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm" ]]; then
  ROUTE_PM=("$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/bin/fallback/pnpm")
elif command -v npm >/dev/null 2>&1; then
  ROUTE_PM=(npm)
else
  echo 'Install Node.js 22+ and npm or pnpm, then run this launcher again.'
  exit 1
fi
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r backend/requirements.txt
fi
if [[ ! -d frontend/node_modules ]]; then
  (cd frontend && "${ROUTE_PM[@]}" install)
fi
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
ROUTE_BACKEND_PID=$!
ROUTE_FRONTEND_PID=''
cleanup() {
  kill "$ROUTE_BACKEND_PID" 2>/dev/null || true
  if [[ -n "$ROUTE_FRONTEND_PID" ]]; then kill "$ROUTE_FRONTEND_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM
sleep 1
if ! kill -0 "$ROUTE_BACKEND_PID" 2>/dev/null; then
  echo 'Backend could not start. Check that port 8000 is available.'
  exit 1
fi
echo 'Open http://127.0.0.1:5173/dashboard — Ctrl+C stops both servers.'
if [[ "${ROUTE_PM[0]##*/}" == npm ]]; then
  ROUTE_DEV_ARGS=(run dev -- --host 127.0.0.1 --port 5173 --strictPort)
else
  ROUTE_DEV_ARGS=(run dev --host 127.0.0.1 --port 5173 --strictPort)
fi
(cd frontend && exec "${ROUTE_PM[@]}" "${ROUTE_DEV_ARGS[@]}") &
ROUTE_FRONTEND_PID=$!
wait "$ROUTE_FRONTEND_PID"
