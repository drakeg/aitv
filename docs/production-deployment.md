# Production single-host deployment

This document describes aitv's supported production **single-host / pilot** Docker deployment. It is intended for a small real deployment such as an SMB pilot, not a horizontally scaled or high-availability installation.

The production stack uses:

- Gunicorn as the Django WSGI server;
- WhiteNoise for collected static assets;
- Caddy as a version-pinned reverse proxy with automatic HTTPS;
- the persistent SQLite volume for application data;
- the same optional EPG and notification workers used by development, without source-code bind mounts.

## Scale boundary

SQLite remains the production data store in this deployment profile. The default is therefore one Gunicorn worker with multiple threads. This is appropriate for a small single-host pilot but is not a claim of multi-instance scalability or high availability.

Do not increase Gunicorn workers or run multiple web containers against the same SQLite database without deliberately re-evaluating database locking and the deployment architecture. Moving to a production client/server database is separate future work if measured pilot load requires it.

## Host prerequisites

- Docker Engine or Docker Desktop with Docker Compose v2.
- A public DNS name for an Internet-facing deployment.
- DNS A/AAAA records pointing that hostname to the deployment host.
- Inbound TCP 80 and 443 reachable by Caddy for certificate issuance/renewal.
- A backup location outside the Docker volume.
- Optional TMDB and SMTP credentials when those features are used.

## Configure production

Create the production environment file:

```bash
cp .env.production.example .env.production
```

Set at minimum:

```dotenv
PUBLIC_HOST=tv.example.com
DJANGO_SECRET_KEY=<long-random-secret>
DJANGO_ALLOWED_HOSTS=tv.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://tv.example.com
```

Never commit `.env.production`. The startup script rejects missing/development placeholder Django secrets.

Validate the configuration before starting:

```bash
docker compose --env-file .env.production -p aitv-production -f compose.production.yml config --quiet
sh -n scripts/start-production.sh
```

## Start the production stack

```bash
docker compose --env-file .env.production -p aitv-production -f compose.production.yml up -d --build
```

The web service:

1. validates required production configuration;
2. runs pending Django migrations;
3. collects static assets;
4. starts Gunicorn on the private Compose network.

Caddy waits for the web healthcheck before proxying traffic and terminates HTTPS. The Django web container is not published directly to the host.

Check status and logs:

```bash
docker compose --env-file .env.production -p aitv-production -f compose.production.yml ps
docker compose --env-file .env.production -p aitv-production -f compose.production.yml logs -f web caddy
```

Verify the public endpoints:

```bash
curl -f https://tv.example.com/health/live/
curl -f https://tv.example.com/health/ready/
```

`/health/live/` verifies the web/database path. `/health/ready/` additionally reflects configured EPG health and can return 503 while the web service remains correctly alive.

## Optional production workers

Enable recurring EPG refreshes:

```bash
docker compose --env-file .env.production -p aitv-production -f compose.production.yml --profile epg up -d --build
```

Enable recurring release notifications:

```bash
docker compose --env-file .env.production -p aitv-production -f compose.production.yml --profile notifications up -d --build
```

Enable both by supplying both profiles.

## Local production smoke test

For a workstation-only smoke test, copy the production example and temporarily use:

```dotenv
PUBLIC_HOST=localhost
HTTP_PORT=8080
HTTPS_PORT=8443
DJANGO_ALLOWED_HOSTS=localhost
DJANGO_CSRF_TRUSTED_ORIGINS=https://localhost:8443
```

Caddy uses a local certificate authority for localhost, so command-line testing may require `curl -k https://localhost:8443/health/live/`. This is only a smoke-test convenience; do not disable certificate verification for a public deployment.

## Security model

The production Compose profile forces:

- `DJANGO_DEBUG=false`;
- HTTPS redirect;
- secure session and CSRF cookies;
- proxy-aware HTTPS detection;
- HSTS with subdomains/preload enabled by default;
- a non-development secret enforced by the startup script;
- no application source bind mount.

Django's `check --deploy --fail-level WARNING` is run in CI against the production security settings. Caddy is the only public HTTP(S) service in the production Compose file.

## Static assets

WhiteNoise serves the collected Django static tree from the Gunicorn application. The startup command runs `collectstatic` before Gunicorn starts, using compressed manifest storage so missing/incorrect static references fail visibly instead of silently producing production-only broken assets.

## Backup

With the standard project name, application data is stored in `aitv-production_aitv_data`. Stop application writers before copying SQLite:

```bash
docker compose --env-file .env.production -p aitv-production -f compose.production.yml stop web epg notifications
docker run --rm \
  -v aitv-production_aitv_data:/data:ro \
  -v "$PWD":/backup \
  alpine sh -c 'cp /data/db.sqlite3 /backup/aitv-production-db.sqlite3'
docker compose --env-file .env.production -p aitv-production -f compose.production.yml start web
```

Restart only the worker profiles that were enabled before the backup. Keep an external/off-host copy for important deployments.

## Upgrade

Before an upgrade, create a database backup and record the currently deployed commit.

```bash
git fetch origin
git switch main
git pull --ff-only origin main
docker compose --env-file .env.production -p aitv-production -f compose.production.yml config --quiet
docker compose --env-file .env.production -p aitv-production -f compose.production.yml up -d --build
```

Then verify container health and both health endpoints. Startup applies migrations before serving requests.

## Rollback

Application rollback and database rollback are separate operations.

- For code-only compatible changes, check out the known-good commit and rebuild.
- If a release applied an incompatible migration, restore the database backup that matches the older code.
- Never assume that checking out old Python code reverses a database migration.

## Secrets

Keep `.env.production` out of Git. Do not place API tokens, SMTP passwords, Django secrets, or provider credentials in Compose files, Docker images, README examples, CI logs, or pull-request text.

## What this deployment does not claim

This profile does not provide:

- horizontal web scaling;
- multi-host failover;
- managed database replication;
- zero-downtime schema migrations;
- external secret-manager integration;
- guaranteed uptime/SLA.

Those should be added only when pilot demand and measured load justify the added infrastructure cost and complexity.
