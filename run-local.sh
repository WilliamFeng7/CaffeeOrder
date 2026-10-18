#!/usr/bin/env bash
# 本地启动管理端和 Java 后端。数据库先执行 docker compose up -d。
set -euo pipefail
OTIA_ROOT="$(cd "$(dirname "$0")" && pwd)"
OTIA_RUN="$OTIA_ROOT/.local-run"
mkdir -p "$OTIA_RUN"

if [ -z "${OTIA_ADMIN_INITIAL_PASSWORD:-}" ]; then
  echo "首次启动前请设置 OTIA_ADMIN_INITIAL_PASSWORD（12–16 个字符）。" >&2
  exit 1
fi

check_port() {
  if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "端口 $1 已被占用；请指定 BACKEND_PORT / ADMIN_PORT，或停止对应服务。" >&2
    exit 1
  fi
}
start_backend() {
  check_port "${BACKEND_PORT:-48080}"
  command -v java >/dev/null
  command -v mvn >/dev/null
  mvn -q -f "$OTIA_ROOT/apps/backend/pom.xml" clean package -DskipTests
  (
    trap '' HUP
    cd "$OTIA_ROOT/apps/backend"
    exec java -jar "$OTIA_ROOT/apps/backend/yudao-server/target/yudao-server.jar" \
      --spring.profiles.active="${CAFE_PROFILE:-dev}" --server.port="${BACKEND_PORT:-48080}"
  ) > "$OTIA_RUN/backend.log" 2>&1 < /dev/null &
  echo "$!" > "$OTIA_RUN/backend.pid"
  echo "后端：http://127.0.0.1:${BACKEND_PORT:-48080}（${CAFE_PROFILE:-dev} 配置）"
}
start_admin() {
  check_port "${ADMIN_PORT:-8080}"
  command -v pnpm >/dev/null
  pnpm --dir "$OTIA_ROOT/apps/admin" install --frozen-lockfile
  (
    trap '' HUP
    cd "$OTIA_ROOT/apps/admin"
    export VITE_PORT="${ADMIN_PORT:-8080}"
    export VITE_PROXY_TARGET="http://127.0.0.1:${BACKEND_PORT:-48080}"
    exec node "$OTIA_ROOT/apps/admin/node_modules/vite/bin/vite.js" --mode development
  ) > "$OTIA_RUN/admin.log" 2>&1 < /dev/null &
  echo "$!" > "$OTIA_RUN/admin.pid"
  echo "管理端：http://127.0.0.1:${ADMIN_PORT:-8080}"
}
case "${1:-all}" in
  all) start_backend; start_admin ;;
  backend) start_backend ;;
  admin) start_admin ;;
  *) echo "用法：$0 [all|backend|admin]" >&2; exit 1 ;;
esac
echo "日志位于 .local-run/，停止请执行 ./stop-local.sh。"
