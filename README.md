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

## Project structure

```text
aitv/
├── content/         # Content catalog, forms, and external content services
├── core/            # Site-level models, admin, and home/dashboard view
├── notifications/   # Notification application foundation
├── streamhub/       # Django project settings, URLs, and WSGI entry point
├── watchlist/       # Per-user watchlist functionality
├── static/          # Site CSS and other static assets
├── templates/       # Shared Django templates
├── manage.py
└── requirements.txt
```

## Requirements

- Python 3.10+
- pip
- A TMDB API key if you want live trending movies

## Local setup

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

The application reads configuration from environment variables. The `.env.example` file documents the supported values. If you use a local `.env` file, export/source it in your shell or use your preferred environment loader before starting Django.

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
| `DJANGO_SECRET_KEY` | development-only fallback | Django signing secret. Set a strong value outside local development. |
| `DJANGO_DEBUG` | `true` | Enables/disables Django debug mode. |
| `DJANGO_ALLOWED_HOSTS` | empty | Comma-separated hostnames accepted by Django. |
| `TMDB_API_KEY` | empty | Enables TMDB trending movie discovery when configured. |
| `TMDB_TIMEOUT_SECONDS` | `5` | Timeout for TMDB HTTP requests. |

When `TMDB_API_KEY` is not configured or TMDB cannot be reached, the dashboard continues to load and simply omits live trending results.

## Testing

Run the Django test suite with:

```bash
python manage.py test
```

Run Django's deployment/configuration checks with:

```bash
python manage.py check
```

GitHub Actions runs these checks for pull requests and pushes to `main`.

## Architecture notes

`core.views.home` assembles the dashboard. Local catalog entries come from `ContentItem`; authenticated users can submit the Quick Add form; watchlist IDs are loaded for the signed-in user; and TMDB discovery is isolated behind `content.services` so external API failures do not take down the page.

The current implementation is intentionally lightweight and uses SQLite for development. Production deployment settings, a production database, static-file serving, authentication UX, and background refresh jobs are future concerns rather than assumptions baked into the development configuration.

## Development roadmap

### Sprint 1 — Foundation and reliability

- [x] Replace hard-coded runtime configuration with environment-driven settings
- [x] Make TMDB integration optional and resilient to network/API failures
- [x] Add baseline automated tests
- [x] Add CI for Django checks and tests
- [x] Document installation, configuration, architecture, and development workflow

### Sprint 2 — Content ingestion and metadata

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

- [ ] Add Docker support and production-oriented settings
- [ ] Add a production database configuration path
- [ ] Add static-file and security-header configuration
- [ ] Add deployment documentation and health checks

## Security

Do not commit real API keys or production secrets. `.env` is ignored by Git; use environment variables or a secrets manager in deployed environments.

## Status

This project is under active development. The current focus is establishing a reliable, testable foundation before expanding content ingestion, personalization, and deployment capabilities.
