#!/usr/bin/env bash
set -euo pipefail


python3 init_db.py

PORT="${PORT:-3000}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-2}"
GUNICORN_THREADS="${GUNICORN_THREADS:-2}"
GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"
BIND="0.0.0.0:${PORT}"

if [ -z "$GUNICORN_WORKERS" ]; then
  if command -v nproc >/dev/null 2>&1; then
    CPU_COUNT=$(nproc)
  else
    CPU_COUNT=1
  fi
  GUNICORN_WORKERS=$(( CPU_COUNT * 2 + 1 ))
fi

if [ -f /app/prestart.sh ]; then
  echo "Running prestart hook"
  /app/prestart.sh
fi

if [ "${1:-}" = "gunicorn" ] || [ "${1:-}" = "" ]; then
  exec gunicorn --preload \
    --bind "${BIND}" app:app \
    --workers "${GUNICORN_WORKERS}" \
    --threads "${GUNICORN_THREADS}" \
    --timeout "${GUNICORN_TIMEOUT}"
else
  exec "$@"
fi

