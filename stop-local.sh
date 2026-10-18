#!/usr/bin/env bash
# 只停止 run-local.sh 记录且命令仍属于此仓库的进程。
set -euo pipefail
OTIA_ROOT="$(cd "$(dirname "$0")" && pwd)"
for service in backend admin; do
  pid_file="$OTIA_ROOT/.local-run/$service.pid"
  [ -f "$pid_file" ] || continue
  pid="$(cat "$pid_file")"
  if [[ "$pid" =~ ^[0-9]+$ ]]; then
    process_command="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    case "$process_command" in
      *"$OTIA_ROOT/apps/backend/yudao-server/target/yudao-server.jar"*|*"$OTIA_ROOT/apps/admin/node_modules/vite/bin/vite.js"*)
        kill "$pid" 2>/dev/null || true
        echo "已停止 $service。"
        ;;
    esac
  fi
  rm -f "$pid_file"
done
