# AI TV / StreamHub

AI TV is a Django-based personal streaming dashboard for discovering movies, TV shows, and web video across multiple sources, maintaining a local catalog, tracking where titles are available, and keeping a separate watchlist for each user.

## Current capabilities

- Multi-source catalog with explicit movie, TV, and web-video types
- Rich title metadata including description, release year, rating, source identity, poster, and genre
- Separate provider availability records so one title can have multiple watch options without being duplicated
- TMDB weekly trending movie and TV discovery when an API key is configured
- Mixed local/container demo catalog with movies, TV shows, YouTube, TMDB examples, and free Internet Archive sources
- Robust YouTube URL/video-ID detection and automatic thumbnails
- One-click TMDB movie/TV discovery import into the managed library
- Authenticated add/edit/delete controls for managed content
- Built-in account registration, login, and logout flows
- Dedicated per-user watchlist page with POST-only add/remove actions
- Django admin support for catalog and availability data
- SQLite development database
- Fast Docker Compose local workflow with configurable host port
- Automated Django checks and tests in GitHub Actions

## Project structure

```text
aitv/
├── content/         # Catalog, provider availability, forms, discovery services, and demo data
├── core/            # Site-level models, dashboard, registration, and tests
├── notifications/   # Notification application foundation
├── streamhub/       # Django project settings, URLs, and WSGI entry point
├── watchlist/       # Per-user watchlist page and controls
├── static/          # Site CSS and static assets
├── templates/       # Shared, account, content, and watchlist templates
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Quick local testing with Docker

```bash
git clone https://github.com/drakeg/aitv.git
cd aitv
cp .env.example .env
docker compose up --build
```

The container automatically runs migrations, refreshes the idempotent demo catalog, and starts Django. The default site is `http://127.0.0.1:8000/`.

To use another host port, set `APP_PORT` in `.env`, for example:

```dotenv
APP_PORT=8007
```

Set `LOAD_DEMO_CONTENT=false` for an empty catalog. You can manually refresh the demo catalog with:

```bash
docker compose run --rm web python manage.py seed_demo_content
```

The source tree is bind-mounted, so normal Python/template/static changes are picked up by Django's development reloader without rebuilding the image. Rebuild when dependencies or the Dockerfile change.

Useful commands:

```bash
docker compose up -d --build
docker compose logs -f web
docker compose run --rm web python manage.py test
docker compose run --rm web python manage.py createsuperuser
docker compose down
```

## Accounts and watchlists

Use **Register** in the navigation bar to create a normal StreamHub account. Registration signs the new user in immediately. Existing users can use the dedicated login page; logout is a CSRF-protected POST action.

Each signed-in user has an independent watchlist at `/watchlist/`. Catalog cards add and remove titles using POST-only controls, and the dedicated watchlist page provides a focused saved-title view.

## Content and discovery workflow

Quick Add accepts a title, URL, genre, and content type. Supported YouTube URL shapes include `youtube.com/watch`, `youtu.be`, Shorts, embeds, and mobile URLs, with strict video-ID character validation.

The catalog stores a title once while `ContentAvailability` records represent individual providers/watch locations. This allows a movie or TV series to gain additional sources later without creating duplicate title cards.

With `TMDB_API_KEY` configured, the dashboard displays separate trending movie and TV rows. Discovery cards can be imported into the managed library while retaining TMDB identity and metadata. TMDB failures or a missing API key do not prevent the dashboard from loading.

The local demo data intentionally exercises multiple source types, including free Internet Archive availability, so Docker testing is useful without external API credentials.

## Standard local setup

```bash
git clone https://github.com/drakeg/aitv.git
cd aitv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

On Windows PowerShell use `.venv\Scripts\Activate.ps1` to activate the environment. Django admin is available at `/admin/`; create an admin with `python manage.py createsuperuser` when needed.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_PORT` | `8000` | Host port exposed by Docker Compose. |
| `DJANGO_SECRET_KEY` | development-only fallback | Django signing secret. |
| `DJANGO_DEBUG` | `true` | Enables/disables Django debug mode. |
| `DJANGO_ALLOWED_HOSTS` | empty outside Compose | Comma-separated accepted hostnames. |
| `TMDB_API_KEY` | empty | Enables TMDB movie and TV discovery. |
| `TMDB_TIMEOUT_SECONDS` | `5` | Timeout for TMDB requests. |
| `LOAD_DEMO_CONTENT` | `true` in Compose | Loads/refreshes demo catalog data at startup. |

## Testing

```bash
python manage.py check
python manage.py test
```

Or through Docker:

```bash
docker compose run --rm web python manage.py test
```

GitHub Actions runs Django checks and the test suite for pull requests and pushes to `main`.

## Architecture notes

`core.views.home` assembles local catalog rows and external TMDB discovery. `ContentItem` represents a movie, TV title, or web video; `ContentAvailability` represents individual providers or watch URLs. The `content` app owns ingestion, discovery normalization, editing, and imports. The `watchlist` app owns user-specific saved titles. Django's built-in authentication system provides sessions and credentials while project templates provide the user-facing account flows.

The Docker path remains development-focused: Django's development server, bind-mounted source, SQLite, and optional demo data. Production container/server, database, static serving, security headers, and health checks remain deployment work.

## Development roadmap

### Sprint 1 — Foundation and reliability

- [x] Environment-driven runtime configuration
- [x] Resilient optional TMDB integration
- [x] Baseline automated tests and CI
- [x] Installation/configuration/architecture documentation
- [x] Fast Docker Compose local workflow

### Sprint 2 — Content ingestion and metadata

- [x] Repeatable mixed-source demo content
- [x] Hardened URL parsing and YouTube extraction
- [x] Rich content metadata and explicit movie/TV/video types
- [x] Separate provider availability model
- [x] Edit/delete flows for managed content
- [x] Movie and TV discovery-to-library ingestion

### Sprint 3 — User experience

- [x] Complete login/logout/registration flows
- [x] Dedicated watchlist page and safer watchlist controls
- [ ] Improve filtering/search and category browsing
- [ ] Add useful empty/error/loading states

### Sprint 4 — Deployment readiness

- [ ] Production-oriented container/settings path
- [ ] Production database configuration path
- [ ] Static-file and security-header configuration
- [ ] Deployment documentation and health checks

## Security

Do not commit real API keys or production secrets. `.env` is ignored by Git; use environment variables or a secrets manager in deployed environments. State-changing catalog and watchlist actions use POST requests with Django CSRF protection.

## Status

The project now has a multi-source movie/TV/video catalog and functional user accounts. Current work is focused on browsing/search UX before deployment hardening.
