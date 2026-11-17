#!/bin/sh
set -eu

interval="${EPG_REFRESH_INTERVAL_SECONDS:-1800}"
regions="${EPG_REGIONS:-US}"
retention="${EPG_RETENTION_HOURS:-6}"
days="${EPG_DAYS:-2}"

case "$interval" in
  ""|*[!0-9]*)
    echo "EPG_REFRESH_INTERVAL_SECONDS must be a positive integer; using 1800." >&2
    interval=1800
    ;;
  0)
    echo "EPG_REFRESH_INTERVAL_SECONDS must be greater than zero; using 1800." >&2
    interval=1800
    ;;
esac

case "$retention" in
  ""|*[!0-9]*)
    echo "EPG_RETENTION_HOURS must be a non-negative integer; using 6." >&2
    retention=6
    ;;
esac

case "$days" in
  ""|*[!0-9]*)
    echo "EPG_DAYS must be an integer from 1 to 7; using 2." >&2
    days=2
    ;;
  0|8|9|[1-9][0-9]*)
    echo "EPG_DAYS must be between 1 and 7; using 2." >&2
    days=2
    ;;
esac

until [ -f /data/db.sqlite3 ]; do
  sleep 2
done

while true; do
  if ! python manage.py refresh_epg --regions "$regions" --retention-hours "$retention" --days "$days"; then
    echo "EPG refresh failed; retrying after $interval seconds." >&2
  fi
  sleep "$interval"
done
