# Docker deployment and operations

This document describes the currently supported Docker deployment model for aitv in a platform-neutral way. It applies to Docker Engine / Docker Desktop environments that support Docker Compose v2.

The current Compose stack is intentionally development-focused. It is suitable for local testing, evaluation, and controlled single-host use. It is **not yet the project's declared production deployment architecture**. Production-serving concerns such as a production WSGI/ASGI server, reverse proxy/TLS termination, production database selection, static-file serving, centralized secrets, and deployment rollback are tracked separately in the backlog.

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

The persistent SQLite database should be backed up before risky upgrades or manual data operations.

For the current single-host development model, the safest basic procedure is:

1. Stop application services so the SQLite file is quiescent.
2. Copy the database out of the named volume.
3. Restart the services.

Example backup:

```bash
docker compose stop
docker run --rm \
  -v aitv_aitv_data:/data:ro \
  -v "$PWD":/backup \
  alpine sh -c 'cp /data/db.sqlite3 /backup/aitv-db.sqlite3'
docker compose start
```

Restore only when you intend to replace the active database:

```bash
docker compose down
docker run --rm \
  -v aitv_aitv_data:/data \
  -v "$PWD":/backup:ro \
  alpine sh -c 'cp /backup/aitv-db.sqlite3 /data/db.sqlite3'
docker compose up -d
```

If the Compose project name is customized, adjust the volume name accordingly.

For important deployments, also keep an external copy of backups and test restore procedures periodically.

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

The current Compose stack remains a development/single-host deployment model. The production-readiness backlog covers the remaining work before the project should claim a supported Internet-facing production deployment.
