#!/bin/sh
set -eu

project_name="${AITV_BACKUP_SMOKE_PROJECT:-aitv-backup-smoke}"
compose_file="${AITV_BACKUP_SMOKE_COMPOSE_FILE:-compose.production.yml}"
env_file="${AITV_BACKUP_SMOKE_ENV_FILE:-.env.production.example}"
backup_dir="$(pwd)/.aitv-backup-smoke-$$"
volume_name="${project_name}_aitv_data"

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
  --profile backups build backups

image_id="$(docker compose --env-file "$env_file" -p "$project_name" -f "$compose_file" \
  --profile backups images -q backups)"
if [ -z "$image_id" ]; then
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
docker run --rm \
  -v "$backup_file:/backup.sqlite3:ro" \
  "$image_id" \
  python -c "import sqlite3; db=sqlite3.connect('file:/backup.sqlite3?mode=ro', uri=True); value=db.execute('select value from smoke').fetchone()[0]; db.close(); assert value == 'backup-profile-smoke', value"

echo "Production backup profile smoke test passed."
