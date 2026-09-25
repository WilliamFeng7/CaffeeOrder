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
STUDENT_PORT=5173
ADMIN_PORT=8080
BARISTA_PORT=8081

# --- 1. Backend virtualenv -------------------------------------------------
if [ ! -x apps/backend/.venv/bin/python ]; then
  echo "==> creating Python 3.12 virtualenv with uv"
  uv venv --python 3.12 apps/backend/.venv
fi
echo "==> installing backend dependencies"
# greenlet: SQLAlchemy asyncio extra, missing from requirements.txt
# bcrypt 4.0.1: passlib 1.7.4 is incompatible with bcrypt >= 4.1
uv pip install --python apps/backend/.venv/bin/python -q \
  -r apps/backend/requirements.txt greenlet "bcrypt==4.0.1"

# --- 2. Local database -----------------------------------------------------
# app/database.py defaults to apps/backend/coffee.db (a DATABASE_URL pointing at a
# path containing "/data" would try to create a Linux-only /data volume directory).
if [ ! -f apps/backend/coffee.db ]; then
  if [ -f data/coffee.db ]; then
    echo "==> seeding apps/backend/coffee.db from data/coffee.db"
    cp -p data/coffee.db apps/backend/coffee.db
  else
    echo "!!  no database found - run the backend once so tables get created"
  fi
fi

# --- 3. Node dependencies --------------------------------------------------
if [ ! -d node_modules ]; then
  echo "==> installing npm workspace dependencies"
  npm install
fi

start_backend() {
  echo "==> backend    http://localhost:$BACKEND_PORT  (docs: /docs)"
  ( cd apps/backend && nohup .venv/bin/python -m uvicorn main:app \
      --host 127.0.0.1 --port "$BACKEND_PORT" > "$ROOT/backend.log" 2>&1 & )
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
    sleep 3
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
echo "API      http://localhost:$BACKEND_PORT/docs"
echo
echo "Demo logins (all password 89129885): admin / student / barista"
