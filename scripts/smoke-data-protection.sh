#!/bin/sh
set -eu

project_name="${AITV_DATA_SMOKE_PROJECT:-aitv-data-smoke}"
compose_file="${AITV_DATA_SMOKE_COMPOSE_FILE:-compose.production.yml}"
env_file="${AITV_DATA_SMOKE_ENV_FILE:-.env.production.example}"
backup_dir="$(pwd)/.aitv-data-smoke-$$"
volume_name="${project_name}_aitv_data"
restore_refusal_log="$backup_dir/restore-refusal.log"

export BACKUP_DIR="$backup_dir"

cleanup() {
  docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
    --profile backups down -v --remove-orphans >/dev/null 2>&1 || true
  docker volume rm "$volume_name" >/dev/null 2>&1 || true
  rm -rf "$backup_dir"
}
trap cleanup EXIT INT TERM

mkdir -p "$backup_dir"

docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  --profile backups build web backups

image_id="$(docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  --profile backups config --images | awk '/-backups$/ { print; exit }')"
if [ -z "$image_id" ] || ! docker image inspect "$image_id" >/dev/null 2>&1; then
  echo "Unable to determine the production backup image." >&2
  exit 1
fi

docker volume create "$volume_name" >/dev/null

docker run --rm \
  -v "$volume_name:/data" \
  "$image_id" \
  python -c "import sqlite3; db=sqlite3.connect('/data/db.sqlite3'); db.execute('create table smoke(value text not null)'); db.execute('insert into smoke values (?)', ('backup-profile-smoke',)); db.commit(); db.close()"

docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  --profile backups run --rm --no-deps backups \
  python -m scripts.backup_worker --once

backup_count="$(find "$backup_dir" -maxdepth 1 -type f -name 'aitv-production-*.sqlite3' | wc -l | tr -d ' ')"
if [ "$backup_count" -ne 1 ]; then
  echo "Expected exactly one scheduled backup, found $backup_count." >&2
  exit 1
fi

docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  --profile backups run --rm --no-deps backups \
  python -m scripts.backup_health

backup_file="$(find "$backup_dir" -maxdepth 1 -type f -name 'aitv-production-*.sqlite3' -print -quit)"
backup_name="$(basename "$backup_file")"

docker run --rm \
  -v "$backup_file:/backup.sqlite3:ro" \
  "$image_id" \
  python -c "import sqlite3; db=sqlite3.connect('file:/backup.sqlite3?mode=ro', uri=True); value=db.execute('select value from smoke').fetchone()[0]; db.close(); assert value == 'backup-profile-smoke', value"

docker run --rm \
  -v "$volume_name:/data" \
  "$image_id" \
  python -c "import sqlite3; db=sqlite3.connect('/data/db.sqlite3'); db.execute('update smoke set value=?', ('mutated-after-backup',)); db.commit(); db.close()"

if docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  run --rm --no-deps \
  -v "$backup_dir:/backup:ro" \
  web python /app/scripts/sqlite_backup.py restore \
  --input "/backup/$backup_name" \
  --target /data/db.sqlite3 \
  >"$restore_refusal_log" 2>&1; then
  echo "Restore unexpectedly succeeded without --confirm-offline." >&2
  exit 1
fi

if ! grep -q -- '--confirm-offline' "$restore_refusal_log"; then
  cat "$restore_refusal_log" >&2
  echo "Restore refusal did not explain the offline confirmation requirement." >&2
  exit 1
fi

docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  run --rm --no-deps \
  -v "$backup_dir:/backup:ro" \
  web python /app/scripts/sqlite_backup.py restore \
  --input "/backup/$backup_name" \
  --target /data/db.sqlite3 \
  --confirm-offline

docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  run --rm --no-deps web \
  python -c "import glob, sqlite3; active=sqlite3.connect('/data/db.sqlite3'); active_value=active.execute('select value from smoke').fetchone()[0]; active.close(); assert active_value == 'backup-profile-smoke', active_value; safety=glob.glob('/data/db.pre-restore-*.sqlite3'); assert len(safety) == 1, safety; previous=sqlite3.connect('file:' + safety[0] + '?mode=ro', uri=True); previous_value=previous.execute('select value from smoke').fetchone()[0]; previous.close(); assert previous_value == 'mutated-after-backup', previous_value"

echo "Production backup and guarded restore smoke test passed."
