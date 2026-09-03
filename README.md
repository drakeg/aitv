# AI TV / StreamHub

AI TV is a Django-based personal streaming dashboard for discovering movies, TV shows, and web video across multiple sources, maintaining a local catalog, tracking where titles are actually available, and keeping a separate watchlist for each user.

The goal is fewer clicks to legitimate content. TMDB is treated as metadata/discovery rather than the final destination whenever a direct network or streaming-provider URL is available.

## Current capabilities

- Multi-source catalog with explicit movie, TV, and web-video types
- Rich title metadata including description, release year, rating, source identity, poster, and genre
- Separate `ContentAvailability` records so a title can have multiple watch destinations without duplicate catalog entries
- Provider-first card actions that link directly to known network/streaming sources
- Automatic provider recognition for ABC, CBS, NBC, FOX, PBS, The CW, YouTube, Internet Archive, Tubi, Pluto TV, Paramount+, Peacock, Hulu, Disney+, Max, Netflix, Prime Video, Apple TV, and Plex URLs
- Dedicated **Watch on Networks** row for local titles with ABC/CBS/NBC/FOX/PBS/CW availability
- TMDB weekly trending movie and TV discovery, visually treated as discovery/details rather than a watch destination
- Support for either a TMDB API key or TMDB Read Access Token; both are not required
- Mixed local/container demo catalog with movies, TV shows, YouTube, Internet Archive, CBS, PBS, FOX, and TMDB metadata examples
- Robust YouTube URL/video-ID detection and automatic thumbnails
- One-click TMDB movie/TV discovery import into the managed library
- Authenticated add/edit/delete controls for managed content
- Built-in account registration, login, and logout flows
- Dedicated per-user watchlist page with provider-first watch actions
- Django admin support for catalog and availability data
- SQLite development database
- Fast Docker Compose local workflow with configurable host port
- Automated Django checks and tests in GitHub Actions

## Project structure

```text
aitv/
├── content/         # Catalog, provider detection/availability, forms, TMDB discovery, and demo data
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

Each signed-in user has an independent watchlist at `/watchlist/`. Catalog cards add and remove titles using POST-only controls. Saved titles retain their direct provider buttons on the watchlist page rather than forcing the user back through a metadata site.

## Direct-source workflow

Quick Add accepts a title, URL, genre, and content type. When the URL belongs to a recognized provider or network, StreamHub automatically creates a matching availability record and labels the card with the appropriate direct action. Examples include **Watch on PBS**, **Open CBS**, **Watch on Tubi**, or **Open Netflix**.

Provider detection uses exact/suffix hostname checks rather than loose string matching, so look-alike domains such as `cbs.com.example.com` are not recognized as CBS.

The initial direct-source adapter list includes:

- Broadcast/network: ABC, CBS, NBC, FOX, PBS, The CW
- Free/ad-supported: Tubi, Pluto TV, Internet Archive, YouTube
- Subscription/streaming: Paramount+, Peacock, Hulu, Disney+, Max, Netflix, Prime Video, Apple TV, Plex

This layer does not bypass authentication, subscriptions, regional restrictions, or DRM. It simply takes the user to the legitimate provider destination as directly as the stored URL allows.

## TMDB workflow

TMDB supplies discovery and metadata. Its cards are labeled **Discovery metadata** and use a subdued **TMDB details** link instead of pretending TMDB is the place to watch the title.

Configure either credential below; both are not required:

```dotenv
# Option 1: API v3 key
TMDB_API_KEY=your_key_here

# Option 2: API Read Access Token
TMDB_READ_ACCESS_TOKEN=your_read_token_here
```

If both are configured, StreamHub prefers the Read Access Token and falls back to the API key otherwise. Docker Compose loads `.env`, so either credential works in the container workflow.

TMDB failures or missing credentials do not prevent the dashboard from loading; live trending rows simply remain empty.

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

`core.views.home` assembles local catalog rows and external TMDB discovery. `ContentItem` represents a movie, TV title, or web video. `ContentAvailability` represents direct network/provider destinations. `content.providers` recognizes supported provider URLs and can automatically attach a direct availability record when content is added.

TMDB remains a metadata/discovery adapter. Direct watch destinations are deliberately modeled separately so additional network feeds, provider APIs, Plex/Jellyfin servers, or other legal sources can be layered onto a title without changing its identity or duplicating it.

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

### Sprint 3 — User experience and direct sources

- [x] Complete login/logout/registration flows
- [x] Dedicated watchlist page and safer watchlist controls
- [x] Provider-first card/watchlist actions
- [x] Initial broadcast-network and streaming-provider URL adapters
- [ ] Improve filtering/search and category browsing
- [ ] Add useful empty/error/loading states
- [ ] Expand source adapters and provider availability ingestion

### Sprint 4 — Deployment readiness

- [ ] Production-oriented container/settings path
- [ ] Production database configuration path
- [ ] Static-file and security-header configuration
- [ ] Deployment documentation and health checks

## Security

Do not commit real API keys or production secrets. `.env` is ignored by Git; use environment variables or a secrets manager in deployed environments. State-changing catalog and watchlist actions use POST requests with Django CSRF protection.

## Status

The project now separates metadata/discovery from direct watch destinations. Current work is focused on reducing clicks through provider-aware browsing while expanding legal source coverage.
