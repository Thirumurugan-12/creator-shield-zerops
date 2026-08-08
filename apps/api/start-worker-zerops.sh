#!/bin/sh
set -eu

cd /var/www/apps/api
exec env PYTHONPATH=/var/www/apps/api:/var/www/apps/api/.zerops-deps python -m app.worker
