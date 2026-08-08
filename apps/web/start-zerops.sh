#!/bin/sh
set -eu
cd /var/www/apps/web
exec /var/www/apps/web/node_modules/.bin/next start --hostname 0.0.0.0 --port 3000
