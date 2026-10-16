#!/usr/bin/env bash
# Deploy an isolated Student demo to an Ubuntu amd64 server on port 5001.
# Usage: bash deploy/demo/deploy.sh [ubuntu@host] [source-menu.db]
set -euo pipefail
cd "$(dirname "$0")/../.."
remote_host=${1:-ubuntu@150.158.121.81}
source_db=${2:-apps/backend/coffee.db}
release_id=$(date -u +%Y%m%dT%H%M%SZ)
remote_release="/home/ubuntu/coffee-order-demo/releases/$release_id"
bundle_dir=$(mktemp -d "${TMPDIR:-/tmp}/coffee-demo.XXXXXX")
trap 'rm -rf "$bundle_dir"' EXIT

npm run build -w apps/frontend/Student
mkdir -p "$bundle_dir/web" "$bundle_dir/static"
cp -R apps/frontend/Student/dist/. "$bundle_dir/web/"
cp -R apps/backend/static/menu "$bundle_dir/static/"
cp apps/backend/static/default.png "$bundle_dir/static/"
python3 deploy/demo/prepare-db.py "$source_db" "$bundle_dir/seed.db"
(
  cd apps/backend
  CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags='-s -w' -o "$bundle_dir/server" ./cmd/server
)
COPYFILE_DISABLE=1 tar --format=ustar --no-xattrs -czf "$bundle_dir/release.tgz" -C "$bundle_dir" server web static seed.db
ssh "$remote_host" "mkdir -p '$remote_release'"
scp "$bundle_dir/release.tgz" "$remote_host:$remote_release/release.tgz"
ssh "$remote_host" bash -s -- "$remote_release" <<'REMOTE'
set -euo pipefail
release_dir=$1
app_root=/home/ubuntu/coffee-order-demo
tar -xzf "$release_dir/release.tgz" -C "$release_dir"
rm "$release_dir/release.tgz"
mkdir -p "$app_root/data"
if [ ! -f "$app_root/data/coffee.db" ]; then
  cp "$release_dir/seed.db" "$app_root/data/coffee.db"
fi
python3 - "$app_root" <<'PY'
import os
import secrets
import sys
from pathlib import Path
root = Path(sys.argv[1])
env = root / 'demo.env'
if not env.exists():
    fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as f:
        f.write(f'SECRET_KEY={secrets.token_urlsafe(48)}\n')
        f.write('DEMO_MODE=true\n')
        f.write(f'DATABASE_URL={root}/data/coffee.db\n')
        f.write(f'STUDENT_WEB_DIR={root}/current/web\n')
        f.write('FORWARDED_ALLOW_IPS=127.0.0.1\n')
PY
ln -sfn "$release_dir" "$app_root/current"
sudo tee /etc/systemd/system/coffee-order-demo.service >/dev/null <<'UNIT'
[Unit]
Description=CoffeeOrder demonstration on port 5001
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/coffee-order-demo/current
EnvironmentFile=/home/ubuntu/coffee-order-demo/demo.env
ExecStart=/home/ubuntu/coffee-order-demo/current/server -addr 0.0.0.0:5001 -dir /home/ubuntu/coffee-order-demo/current
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/ubuntu/coffee-order-demo/data

[Install]
WantedBy=multi-user.target
UNIT
if [ -f /etc/systemd/system/coffee-order-demo.service.d/preview.conf ]; then
  sudo rm /etc/systemd/system/coffee-order-demo.service.d/preview.conf
fi
sudo systemctl daemon-reload
sudo systemctl enable coffee-order-demo.service
sudo systemctl restart coffee-order-demo.service
for attempt in 1 2 3 4 5; do
  if curl --fail --silent http://127.0.0.1:5001/api/v1/app/config; then
    printf '\n'
    sudo systemctl is-active coffee-order-demo.service
    exit 0
  fi
  sleep 1
done
sudo journalctl -u coffee-order-demo.service -n 20 --no-pager
exit 1
REMOTE
printf 'Demo deployed to http://%s:5001\n' "${remote_host#*@}"
