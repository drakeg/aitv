# AI TV / StreamHub

AI TV is a Django-based personal streaming dashboard for discovering movies and TV from live upstream sources, tracking where titles are actually available, and keeping a separate watchlist for each user.

The goal is fewer clicks to legitimate content. TMDB is treated as metadata/discovery rather than the final destination whenever a direct network or streaming-provider URL is available.

## Current capabilities

- Live US TV schedule discovery from TVmaze
- Live free-movie discovery from the Internet Archive
- Live TMDB trending movie and TV discovery
- TMDB trending cards enriched with runtime, TV network/episode context, and current US provider availability when supplied upstream
- Compact provider presentation: two watch-source badges are shown on-card, with additional sources summarized instead of stretching card height
- Provider-first card actions and direct network/service destinations where a legitimate source exposes them
- Per-user discovery preferences from the Profile page, including Comedy, Crime, Drama, News, Reality, and other supported categories
- Per-user watchlists using the same shared card presentation as the main dashboard
- Automatic provider recognition for ABC, CBS, NBC, FOX, PBS, The CW, YouTube, Internet Archive, Tubi, Pluto TV, Paramount+, Peacock, Hulu, Disney+, Max, Netflix, Prime Video, Apple TV, and Plex URLs
- Account registration, login, logout, Profile, and watchlist flows
- SQLite development database
- Fast Docker Compose local workflow with configurable host port
- Automated Django checks and tests in GitHub Actions

## Live-data policy

The main dashboard is **live-source only**. It does not render seeded examples, manually seeded demo rows, or local sample catalog sections. Search on the dashboard searches the currently fetched live discovery results rather than the local database.

Older development versions created nine sample rows at container startup. The current migration removes those known legacy demo rows, the demo seeder has been removed, and Docker no longer has a demo-data startup path.

The local `ContentItem`/`ContentAvailability` models remain because they are used to persist watchlist/imported metadata and support provider-aware saved items. Persisted user data is not used as a substitute for live discovery on the home page.

When an upstream source does not provide a field, the UI says that the value is not listed rather than inventing it. Provider availability can vary by title and region.

## Project structure

```text
aitv/
├── content/         # Catalog persistence, provider detection, and live source adapters
├── core/            # Dashboard, profile/preferences, registration, and tests
├── notifications/   # Notification application foundation
├── streamhub/       # Django project settings, URLs, and WSGI entry point
├── watchlist/       # Per-user watchlist page and controls
├── static/          # Site CSS and JavaScript
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

The container automatically runs migrations and starts Django. It does **not** load sample/demo content. The default site is `http://127.0.0.1:8000/`.

To use another host port, set `APP_PORT` in `.env`, for example:

```dotenv
APP_PORT=8007
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

## Accounts, watchlists, and discovery preferences

Use **Register** in the navigation bar to create an account. Registration signs the new user in immediately. Existing users can use the dedicated login page; logout is a CSRF-protected POST action.

Each signed-in user has an independent watchlist at `/watchlist/`. The watchlist reuses the same shared provider-first card partial as the main dashboard.

Discovery tuning is per-user and lives under **Profile**. The public/default experience does not globally suppress News or any other category. One user's selections never affect another account.

## Live source workflow

### TVmaze

TVmaze supplies today's US schedule plus show/network/service, episode, runtime, airtime, genres, and official show destinations where available. Cards prefer the official network/service destination instead of another metadata hop.

### Internet Archive

The Internet Archive adapter pulls current public movie records from its search endpoint and links directly to playable item pages.

### TMDB

TMDB supplies trending movie/TV discovery and metadata. Configure either credential below; both are not required:

```dotenv
TMDB_API_KEY=your_key_here
# or
TMDB_READ_ACCESS_TOKEN=your_read_token_here
```

Trending cards request additional current watch context so they can show runtime, TV network/episode information, and US provider availability. Provider rows are intentionally compact: at most two are shown directly on a card, with a `+N more` summary and a **See watch options** action when TMDB provides a watch URL.

TMDB failures or missing credentials do not prevent the dashboard from loading; affected live rows remain empty or show an unavailable state.

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
| `TMDB_API_KEY` | empty | Optional TMDB v3 API-key authentication. |
| `TMDB_READ_ACCESS_TOKEN` | empty | Optional TMDB Bearer-token authentication; preferred when set. |
| `TMDB_TIMEOUT_SECONDS` | `5` | TMDB request timeout fallback. |
| `SOURCE_TIMEOUT_SECONDS` | `5` | Shared upstream-source timeout. |

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

`core.views.home` assembles only live discovery arrays from TVmaze, Internet Archive, and TMDB. `ContentItem` persists imported/saved title metadata. `ContentAvailability` persists provider destinations for saved items. `content.providers` recognizes supported provider URLs.

The dashboard does not fall back to seeded/local catalog rows when live data is unavailable. That keeps the UI truthful about what came from an actual upstream source.

The Docker path remains development-focused: Django's development server, bind-mounted source, and SQLite. Production container/server, database, static serving, security headers, and health checks remain deployment work.

## Development roadmap

### Sprint 1 — Foundation and reliability

- [x] Environment-driven runtime configuration
- [x] Resilient optional TMDB integration
- [x] Baseline automated tests and CI
- [x] Installation/configuration/architecture documentation
- [x] Fast Docker Compose local workflow

### Sprint 2 — Content ingestion and metadata

- [x] Hardened URL parsing and YouTube extraction
- [x] Rich content metadata and explicit movie/TV/video types
- [x] Separate provider availability model
- [x] Edit/delete flows for managed content
- [x] Movie and TV discovery-to-library ingestion

### Sprint 3 — User experience and direct sources

- [x] Complete login/logout/registration flows
- [x] Dedicated watchlist page and safer watchlist controls
- [x] Provider-first card/watchlist actions
- [x] Initial broadcast-network and streaming-provider URL adapters
- [x] Per-user discovery preferences and Profile
- [x] Live-source-only dashboard
- [x] Compact enriched trending cards
- [ ] Expand legal live-source adapters and direct provider availability ingestion

### Sprint 4 — Deployment readiness

- [ ] Production-oriented container/settings path
- [ ] Production database configuration path
- [ ] Static-file and security-header configuration
- [ ] Deployment documentation and health checks

## Security

Do not commit real API keys or production secrets. `.env` is ignored by Git; use environment variables or a secrets manager in deployed environments. State-changing catalog and watchlist actions use POST requests with Django CSRF protection.

## Status

The project now uses live upstream discovery on the home page, keeps metadata links secondary, and focuses on consistent provider-aware cards with per-user tuning.
