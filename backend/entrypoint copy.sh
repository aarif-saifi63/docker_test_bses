#!/usr/bin/env bash
set -euo pipefail


python3 init_db.py

PORT="${PORT:-3000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
GUNICORN_WORKER_CONNECTIONS="${GUNICORN_WORKER_CONNECTIONS:-1000}"
BIND="0.0.0.0:${PORT}"

# NOTE: With gevent workers, CPU-count-based formulas (2*CPU+1) do NOT apply.
# Gevent handles concurrency via coroutines, not threads/processes.
# 2-4 gevent workers is sufficient regardless of CPU count.

if [ -f /app/prestart.sh ]; then
  echo "Running prestart hook"
  /app/prestart.sh
fi

if [ "${1:-}" = "gunicorn" ] || [ "${1:-}" = "" ]; then
  exec gunicorn \
    --bind "${BIND}" app:app \
    --workers "${GUNICORN_WORKERS}" \
    --worker-class gevent \
    --worker-connections "${GUNICORN_WORKER_CONNECTIONS}" \
    --timeout "${GUNICORN_TIMEOUT}"
else
  exec "$@"
fi


