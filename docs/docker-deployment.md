# Docker deployment and operations

This document describes aitv's Docker development/testing model in a platform-neutral way. It applies to Docker Engine / Docker Desktop environments that support Docker Compose v2.

The default `docker-compose.yml` remains development-focused: Django's development server, source bind mounts, and convenient local iteration. A separate hardened single-host/pilot production stack is now documented in `docs/production-deployment.md` and defined by `compose.production.yml`. Do not use the development Compose file as an Internet-facing production deployment.

## Components

The Compose stack defines three services:

- `web` — Django application, database migrations, and development server.
- `epg` — optional recurring normalized EPG refresh worker, enabled with the `epg` profile.
- `notifications` — optional recurring Favorite-release notification worker, enabled with the `notifications` profile.

All services share the same application image and persistent `aitv_data` volume.

## Prerequisites

- Docker Engine or Docker Desktop with Docker Compose v2.
- Git.
- Network access to the upstream sources you choose to use.
- Optional TMDB credentials for TMDB-backed discovery/provider features.
- Optional SMTP settings for email notification delivery.

Verify Docker before deployment:

```bash
docker version
docker compose version
```

## First deployment

Clone the repository and create a local environment file:

```bash
git clone https://github.com/drakeg/aitv.git
cd aitv
cp .env.example .env
```

Review `.env` before starting. At minimum, choose an available host port and replace the development signing key for any deployment that is not disposable:

```dotenv
APP_PORT=8000
DJANGO_SECRET_KEY=replace-with-a-unique-secret
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
```

Validate the Compose configuration before starting:

```bash
docker compose config --quiet
```

A normal configuration validation should complete without warnings.

Build and start the web service:

```bash
docker compose up -d --build
```

The web container runs database migrations before starting Django.

## Optional worker profiles

Enable recurring EPG refreshes:

```bash
docker compose --profile epg up -d --build
```

Enable recurring Favorite-release checks:

```bash
docker compose --profile notifications up -d --build
```

Enable both optional workers:

```bash
docker compose --profile epg --profile notifications up -d --build
```

Profiles are opt-in. Ordinary `docker compose up -d` starts only the web service.

## Configuration

Use `.env.example` as the canonical list of supported environment variables.

Important groups:

- Web/runtime: `APP_PORT`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.
- SQLite: `SQLITE_DB_PATH`, `SQLITE_TIMEOUT_SECONDS`.
- Source/API access: `TMDB_API_KEY`, `TMDB_READ_ACCESS_TOKEN`, `TMDB_TIMEOUT_SECONDS`, `SOURCE_TIMEOUT_SECONDS`.
- EPG worker: `EPG_REGIONS`, `EPG_REFRESH_INTERVAL_SECONDS`, `EPG_RETENTION_HOURS`, `EPG_DAYS`, `EPG_STALE_AFTER_SECONDS`.
- Notifications: `RELEASE_CHECK_INTERVAL_SECONDS`, SMTP settings, and `DEFAULT_FROM_EMAIL`.

Do not commit real secrets or credentials. The repository ignores `.env`.

## Persistent data

The Compose stack stores SQLite data in the named `aitv_data` volume mounted at `/data`.

Normal shutdown preserves data:

```bash
docker compose down
```

Do **not** use `docker compose down -v` unless you intentionally want to delete the persistent database volume.

Inspect the volume:

```bash
docker volume ls | grep aitv
docker volume inspect aitv_aitv_data
```

The exact Compose-generated volume name can vary if the project name is overridden.

## Health and readiness

The application exposes two operational endpoints:

- `/health/live/` — confirms the Django/database path is alive.
- `/health/ready/` — evaluates database health plus configured EPG freshness/failure state.

The Docker Compose healthcheck uses liveness, not readiness. This prevents an upstream EPG problem from causing a restart loop.

Check container state:

```bash
docker compose ps
```

Check liveness from the host:

```bash
curl -f http://127.0.0.1:${APP_PORT:-8000}/health/live/
```

Check readiness:

```bash
curl -f http://127.0.0.1:${APP_PORT:-8000}/health/ready/
```

A readiness HTTP 503 can indicate missing, failed, or stale EPG refresh state even when the web container itself is healthy.

## Logs and troubleshooting

Follow web logs:

```bash
docker compose logs -f web
```

Follow all active services:

```bash
docker compose logs -f
```

Inspect optional worker logs:

```bash
docker compose logs -f epg
docker compose logs -f notifications
```

Common checks:

```bash
docker compose config --quiet
docker compose ps
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test
```

If the selected host port is already in use, change `APP_PORT` in `.env` and recreate the web container:

```bash
docker compose up -d --build
```

## Manual operations

Run database migrations explicitly:

```bash
docker compose run --rm web python manage.py migrate
```

Create an admin user:

```bash
docker compose run --rm web python manage.py createsuperuser
```

Refresh EPG data once:

```bash
docker compose run --rm web python manage.py refresh_epg
```

Run one Favorite-release check:

```bash
docker compose run --rm web python manage.py check_release_notifications
```

## Updating an existing deployment

Before updating, confirm the working tree is clean if the deployment is a Git checkout:

```bash
git status --short
```

Fetch and fast-forward the deployment branch:

```bash
git fetch origin
git switch main
git pull --ff-only origin main
```

Validate configuration, rebuild, and recreate services:

```bash
docker compose config --quiet
docker compose up -d --build
```

Then verify:

```bash
docker compose ps
curl -f http://127.0.0.1:${APP_PORT:-8000}/health/live/
```

Because migrations run automatically in the web startup command, a normal update applies pending Django migrations before the development server starts.

## Backup and restore

AITV includes `scripts/sqlite_backup.py` for consistent SQLite backup, integrity verification, and guarded offline restore. The helper uses SQLite's backup API rather than copying a live database file.

Create and verify a backup inside the web container, then copy it to the host:

```bash
mkdir -p backups
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose exec -T web python /app/scripts/sqlite_backup.py backup \
  --source /data/db.sqlite3 \
  --output /tmp/aitv-db.sqlite3
docker compose exec -T web python /app/scripts/sqlite_backup.py verify \
  --input /tmp/aitv-db.sqlite3
docker compose cp web:/tmp/aitv-db.sqlite3 "./backups/aitv-$timestamp.sqlite3"
```

For important deployments, keep an additional copy outside the Docker host.

Restore only when you intentionally want to replace the active database. Stop application writers first:

```bash
docker compose stop web epg notifications
```

Then use a one-off container with the backup directory mounted read-only:

```bash
backup_file="aitv-YYYYMMDDTHHMMSSZ.sqlite3"
docker compose run --rm --no-deps \
  -v "$PWD/backups:/backup:ro" \
  web python /app/scripts/sqlite_backup.py restore \
  --input "/backup/$backup_file" \
  --target /data/db.sqlite3 \
  --confirm-offline
docker compose up -d
```

The restore command refuses to proceed without `--confirm-offline`, verifies the supplied backup, preserves a verified pre-restore safety snapshot when a database already exists, replaces the target atomically, and verifies the restored database.

## Rollback

The current Docker path does not yet provide an automated application rollback mechanism.

A manual code rollback can be performed by checking out a previously known-good Git commit and rebuilding:

```bash
git checkout <known-good-commit>
docker compose up -d --build
```

Database compatibility must be considered separately. If a newer version applied incompatible migrations, restore a compatible database backup before running the older code.

Do not treat code rollback alone as a safe database rollback strategy.

## Network exposure

The Compose file publishes the Django development server on the configured host port.

For controlled local/LAN testing, set `DJANGO_ALLOWED_HOSTS` appropriately and apply host firewall/network policy as needed.

Do not expose the current development server directly to the public Internet and call that a production deployment. A production design should explicitly define TLS termination, reverse proxying, production Django serving, static assets, database choice, secrets, logging, and backup/restore policy.

That production-readiness work is tracked in the planned backlog.

## Security notes

- Replace the development `DJANGO_SECRET_KEY` fallback for any durable deployment.
- Set `DJANGO_DEBUG=false` outside development.
- Keep `DJANGO_ALLOWED_HOSTS` scoped to intended hostnames/addresses.
- Do not commit `.env`, API keys, SMTP passwords, or provider credentials.
- aitv does not bypass provider authentication or DRM and should not be configured with scraped or untrusted stream URLs.

## Deployment checklist

Before considering a Docker deployment healthy:

- Repository is on the intended commit/branch.
- `.env` contains the intended non-secret and secret settings.
- `docker compose config --quiet` completes without warnings.
- `docker compose up -d --build` completes successfully.
- `docker compose ps` shows the expected services.
- Web container health becomes `healthy`.
- `/health/live/` returns success.
- `/health/ready/` is understood and monitored if EPG freshness is operationally important.
- Persistent-volume backup expectations are understood.
- Optional worker profiles are enabled only when desired.
- Logs show no unexplained recurring warnings or errors.

## Production status

The default Compose stack remains the supported development/testing path. For a real single-host SMB pilot, use the separate production profile documented in `docs/production-deployment.md`, which uses Gunicorn, WhiteNoise, Caddy/HTTPS, deployment security checks, and no source bind mount.

The production profile deliberately retains SQLite and defaults to one Gunicorn worker, so it is not a horizontal-scaling or high-availability architecture.
