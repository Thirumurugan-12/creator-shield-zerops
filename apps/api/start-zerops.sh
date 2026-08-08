#!/bin/sh
set -eu

cd /var/www/apps/api
export PYTHONPATH=/var/www/apps/api:/var/www/apps/api/.zerops-deps

alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
