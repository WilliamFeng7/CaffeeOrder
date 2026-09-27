#!/usr/bin/env bash
# ------------------------------------------------------------------
# Local development launcher for the CoffeeOrder system.
#
#   ./run-local.sh          start backend + 3 frontends (detached)
#   ./run-local.sh backend   start only the backend
#
# Logs: *.log in the repo root (gitignored). Stop with ./stop-local.sh
# ------------------------------------------------------------------
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"

BACKEND_PORT=8000
# Frontend ports can be changed per run when another project already uses
# one, e.g.  STUDENT_PORT=5174 ./run-local.sh
STUDENT_PORT=${STUDENT_PORT:-5173}
ADMIN_PORT=${ADMIN_PORT:-8080}
BARISTA_PORT=${BARISTA_PORT:-8081}

# --- 1. Backend (Go) --------------------------------------------------------
if ! command -v go >/dev/null 2>&1; then
  echo "!!  Go is not installed. Install it with: brew install go"
  exit 1
fi
echo "==> building the Go backend"
( cd apps/backend && GOPROXY="${GOPROXY:-https://goproxy.cn,direct}" go build -o bin/server ./cmd/server )

# --- 2. Local database -----------------------------------------------------
# The server defaults to apps/backend/coffee.db and creates any missing tables.
if [ ! -f apps/backend/coffee.db ]; then
  if [ -f data/coffee.db ]; then
    echo "==> seeding apps/backend/coffee.db from data/coffee.db"
    cp -p data/coffee.db apps/backend/coffee.db
  else
    echo "==> no database yet: the backend will create an empty one"
    echo "    add the first admin with: (cd apps/backend && go run ./cmd/createuser -username admin -role admin)"
  fi
fi

# --- 3. Node dependencies --------------------------------------------------
if [ ! -d node_modules ]; then
  echo "==> installing npm workspace dependencies"
  npm install
fi

start_backend() {
  echo "==> backend    http://localhost:$BACKEND_PORT"
  ( cd apps/backend && nohup ./bin/server -addr "127.0.0.1:$BACKEND_PORT" -dir . \
      > "$ROOT/backend.log" 2>&1 & )
}

start_frontend() {
  local dir="apps/frontend/$1" port="$2" log="$3"
  echo "==> $1$([ ${#1} -lt 8 ] && printf '%*s' $((8 - ${#1})) '') http://localhost:$port"
  ( cd "$dir" && nohup npx vite --port "$port" --strictPort --host 0.0.0.0 \
      > "$ROOT/$log" 2>&1 & )
}

case "${1:-all}" in
  backend) start_backend ;;
  frontend)
    start_frontend Student "$STUDENT_PORT" student.log
    start_frontend Admin   "$ADMIN_PORT"   admin.log
    start_frontend Barista "$BARISTA_PORT" barista.log
    ;;
  all)
    start_backend
    sleep 1
    start_frontend Student "$STUDENT_PORT" student.log
    start_frontend Admin   "$ADMIN_PORT"   admin.log
    start_frontend Barista "$BARISTA_PORT" barista.log
    ;;
  *) echo "usage: $0 [all|backend|frontend]"; exit 1 ;;
esac

sleep 6
echo
echo "Waiting for services to answer..."
for p in $BACKEND_PORT $STUDENT_PORT $ADMIN_PORT $BARISTA_PORT; do
  code=$(curl -s -o /dev/null -m 5 -w '%{http_code}' "http://127.0.0.1:$p/" || true)
  printf '  port %-5s -> %s\n' "$p" "${code:-no response}"
done
echo
echo "Student  http://localhost:$STUDENT_PORT   (OTIA Café)"
echo "Admin    http://localhost:$ADMIN_PORT   (Coffee Admin)"
echo "Barista  http://localhost:$BARISTA_PORT   (KDS)"
echo "API      http://localhost:$BACKEND_PORT/api/v1"
echo
echo "Demo logins (all password 89129885): admin / student / barista"
