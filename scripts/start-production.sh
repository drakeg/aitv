#!/bin/sh
set -eu

case "${DJANGO_SECRET_KEY:-}" in
  ""|change-me|dev-key-change-me|dev-docker-key-change-me|replace-*)
    echo "DJANGO_SECRET_KEY must be set to a non-development secret for production." >&2
    exit 1
    ;;
esac

if [ -z "${DJANGO_ALLOWED_HOSTS:-}" ]; then
  echo "DJANGO_ALLOWED_HOSTS must be configured for production." >&2
  exit 1
fi

mkdir -p /data /app/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

workers="${GUNICORN_WORKERS:-1}"
threads="${GUNICORN_THREADS:-4}"
timeout="${GUNICORN_TIMEOUT_SECONDS:-30}"

case "$workers" in
  ""|*[!0-9]*|0)
    echo "GUNICORN_WORKERS must be a positive integer; using 1." >&2
    workers=1
    ;;
esac
case "$threads" in
  ""|*[!0-9]*|0)
    echo "GUNICORN_THREADS must be a positive integer; using 4." >&2
    threads=4
    ;;
esac
case "$timeout" in
  ""|*[!0-9]*|0)
    echo "GUNICORN_TIMEOUT_SECONDS must be a positive integer; using 30." >&2
    timeout=30
    ;;
esac

exec gunicorn streamhub.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "$workers" \
  --threads "$threads" \
  --timeout "$timeout" \
  --access-logfile - \
  --error-logfile -
