# AI TV / StreamHub

AI TV is a Django-based personal streaming dashboard for collecting content from multiple sources, browsing curated categories, tracking a per-user watchlist, and supplementing locally stored content with external discovery data such as TMDB trending movies.

## Current capabilities

- Django web dashboard with reusable templates and static assets
- Local `ContentItem` catalog with title, URL, genre, duration, thumbnail, and source type
- Quick Add form for adding content from the home page
- Automatic YouTube detection and thumbnail generation for common YouTube URLs
- TMDB weekly trending movie integration
- Per-user watchlist model with duplicate prevention
- Django admin support for managed data
- SQLite development database
- Docker Compose workflow for fast local testing
- Optional idempotent demo catalog for local/container testing

## Project structure

```text
aitv/
├── content/         # Content catalog, forms, external services, and demo seed command
├── core/            # Site-level models, admin, and home/dashboard view
├── notifications/   # Notification application foundation
├── streamhub/       # Django project settings, URLs, and WSGI entry point
├── watchlist/       # Per-user watchlist functionality
├── static/          # Site CSS and other static assets
├── templates/       # Shared Django templates
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Requirements

For the standard local workflow:

- Python 3.10+
- pip

For the Docker workflow:

- Docker Engine or Docker Desktop
- Docker Compose v2 (`docker compose`)

A TMDB API key is optional and only required for live trending movies.

## Quick local testing with Docker

Docker is the fastest way to bring up the project for local testing.

```bash
git clone https://github.com/drakeg/aitv.git
cd aitv
cp .env.example .env
docker compose up --build
```

The container runs database migrations automatically, loads a small demo catalog, and starts Django on all container interfaces. The demo seed is idempotent, so restarting the container does not create duplicate rows. By default the site is available at `http://127.0.0.1:8000/`.

To use another host port, change `APP_PORT` in `.env`, for example:

```dotenv
APP_PORT=8080
```

Then browse to `http://127.0.0.1:8080/`.

To start with an empty catalog instead, set:

```dotenv
LOAD_DEMO_CONTENT=false
```

You can also seed or refresh the demo catalog manually:

```bash
docker compose run --rm web python manage.py seed_demo_content
```

Because the repository is bind-mounted into the development container, Python/template/static-file changes are available immediately through Django's development reloader without rebuilding the image. Rebuild when dependencies or the Dockerfile change.

Useful Docker commands:

```bash
# Start or rebuild
docker compose up --build

# Start in the background
docker compose up -d --build

# View logs
docker compose logs -f web

# Run the test suite in the container
docker compose run --rm web python manage.py test

# Create an admin user
docker compose run --rm web python manage.py createsuperuser

# Stop containers
docker compose down
```

## Standard local setup

```bash
git clone https://github.com/drakeg/aitv.git
cd aitv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

On Windows PowerShell, activate the virtual environment with:

```powershell
.venv\Scripts\Activate.ps1
```

The application reads configuration from environment variables. The `.env.example` file documents the supported values. If you use a local `.env` file outside Docker Compose, export/source it in your shell or use your preferred environment loader before starting Django.

Run the initial database setup:

```bash
python manage.py migrate
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Then browse to `http://127.0.0.1:8000/`. Django admin is available at `/admin/`.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_PORT` | `8000` | Host port exposed by Docker Compose. |
| `DJANGO_SECRET_KEY` | development-only fallback | Django signing secret. Set a strong value outside local development. |
| `DJANGO_DEBUG` | `true` | Enables/disables Django debug mode. |
| `DJANGO_ALLOWED_HOSTS` | empty outside Compose | Comma-separated hostnames accepted by Django. |
| `TMDB_API_KEY` | empty | Enables TMDB trending movie discovery when configured. |
| `TMDB_TIMEOUT_SECONDS` | `5` | Timeout for TMDB HTTP requests. |
| `LOAD_DEMO_CONTENT` | `true` in Compose | Loads/refreshes a small demo catalog at container startup. |

When `TMDB_API_KEY` is not configured or TMDB cannot be reached, the dashboard continues to load and simply omits live trending results.

## Testing

Run the Django test suite locally with:

```bash
python manage.py test
```

Or run it through Docker:

```bash
docker compose run --rm web python manage.py test
```

Run Django's deployment/configuration checks with:

```bash
python manage.py check
```

GitHub Actions runs these checks for pull requests and pushes to `main`.

## Architecture notes

`core.views.home` assembles the dashboard. Local catalog entries come from `ContentItem`; authenticated users can submit the Quick Add form; watchlist IDs are loaded for the signed-in user; and TMDB discovery is isolated behind `content.services` so external API failures do not take down the page.

The Docker setup intentionally remains development-focused. It uses Django's development server, bind-mounts the working tree for rapid iteration, stores the SQLite database in the repository working directory, and optionally seeds a small local demo catalog. Production deployment settings, a production database, static-file serving, authentication UX, and background refresh jobs remain future concerns.

## Development roadmap

### Sprint 1 — Foundation and reliability

- [x] Replace hard-coded runtime configuration with environment-driven settings
- [x] Make TMDB integration optional and resilient to network/API failures
- [x] Add baseline automated tests
- [x] Add CI for Django checks and tests
- [x] Document installation, configuration, architecture, and development workflow
- [x] Add a fast Docker Compose workflow for local testing

### Sprint 2 — Content ingestion and metadata

- [x] Add repeatable demo content for useful local/container testing
- [ ] Harden URL parsing and YouTube video-ID extraction
- [ ] Add richer content metadata and validation
- [ ] Add edit/delete flows for locally managed content
- [ ] Improve discovery-to-library ingestion so external results can become managed items

### Sprint 3 — User experience

- [ ] Add complete login/logout/registration flows
- [ ] Add a dedicated watchlist page and richer watchlist controls
- [ ] Improve filtering/search and category browsing
- [ ] Add useful empty/error/loading states

### Sprint 4 — Deployment readiness

- [ ] Add production-oriented container/settings path
- [ ] Add a production database configuration path
- [ ] Add static-file and security-header configuration
- [ ] Add deployment documentation and health checks

## Security

Do not commit real API keys or production secrets. `.env` is ignored by Git; use environment variables or a secrets manager in deployed environments.

## Status

This project is under active development. The current focus is expanding reliable content ingestion and local testability on top of the established foundation.
