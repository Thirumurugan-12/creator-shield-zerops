#!/usr/bin/env bash
set -Eeuo pipefail

cd /app/apps/api
PYTHONPATH=/app/apps/api alembic upgrade head

PYTHONPATH=/app/apps/api uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid=$!
PYTHONPATH=/app/apps/api python -m app.worker &
worker_pid=$!

cd /app/apps/web
npm run start -- --hostname 0.0.0.0 --port 3000 &
web_pid=$!

shutdown() {
  kill "$api_pid" "$worker_pid" "$web_pid" 2>/dev/null || true
  wait || true
}
trap shutdown EXIT INT TERM

wait -n "$api_pid" "$worker_pid" "$web_pid"
exit $?
