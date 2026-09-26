#!/usr/bin/env bash
# Stop everything started by ./run-local.sh
set -uo pipefail

for pattern in "bin/server -addr" "uvicorn main:app" "vite --port 5173" "vite --port 8080" "vite --port 8081"; do
  if pkill -f "$pattern" 2>/dev/null; then
    echo "stopped: $pattern"
  else
    echo "not running: $pattern"
  fi
done

sleep 1
lsof -nP -iTCP:8000 -iTCP:5173 -iTCP:8080 -iTCP:8081 -sTCP:LISTEN 2>/dev/null \
  || echo "all ports free"
