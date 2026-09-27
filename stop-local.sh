#!/usr/bin/env bash
# Stop everything started by ./run-local.sh
set -uo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

# Vite servers are matched by this repo's own vite binary, so a dev server of
# another project on the same ports is left alone, and any port works.
for pattern in "bin/server -addr" "uvicorn main:app" "$ROOT/node_modules/.bin/vite"; do
  if pkill -f "$pattern" 2>/dev/null; then
    echo "stopped: ${pattern#$ROOT/}"
  else
    echo "not running: ${pattern#$ROOT/}"
  fi
done

sleep 1
still=$(lsof -nP -iTCP:8000 -iTCP:5173 -iTCP:5174 -iTCP:8080 -iTCP:8081 -sTCP:LISTEN 2>/dev/null)
if [ -n "$still" ]; then
  echo "still listening (not started by this repo, or still shutting down):"
  echo "$still"
else
  echo "all ports free"
fi
