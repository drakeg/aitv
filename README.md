# aitv

aitv is a Django-based personal streaming dashboard for discovering movies and TV from live upstream sources, seeing where titles are actually available, and keeping account-specific Watchlist and Favorite state.

The goal is fewer clicks to legitimate content. Direct network/service destinations are preferred when a source actually supplies them; TMDB is used for discovery, metadata, canonical identity, and regional provider context rather than treated as the viewing destination. A unified Live TV/EPG experience is now being built across legitimate sources: the first normalized region-aware now/next guide is available at `/live-tv/`, and signed-in viewers can Favorite channels and filter the guide to their own Favorites. Source and playback boundaries are documented in `docs/live-tv-epg.md`.

## Current capabilities

- Live US TV schedule discovery from TVmaze, including network/web-channel and episode context when supplied
- Live free-movie discovery from the Internet Archive
- Live TMDB TV and movie discovery, including daily TV trending plus on-the-air/popular TV pools
- Provider-first cards that distinguish direct-watch destinations from metadata/source-detail links
- Regional TMDB provider availability with access types such as Free, Free with ads, Subscription, Rent, and Buy
- Compact provider pills with expandable `+N more` choices instead of stretching card rows
- Per-user US/region availability behavior, category preferences, TV-first/Balanced/Movies-first content mix, and preferred streaming-service ordering/ranking with live `On <provider>` match feedback and provider-specific watch-option labels when the preferred service is the best reported regional choice
- Independent per-user Watchlist and Favorite state; Favorites are prioritized in discovery and can drive release notifications
- Paginated in-app Favorite release notifications plus optional SMTP email delivery
- Optional Docker notification worker for recurring Favorite release checks
- Live-source-only home discovery: no seeded/sample catalog fallback
- Configurable Docker host port and persistent SQLite data volume
- Automated Django checks and tests in GitHub Actions

## Live-data and provider policy

The dashboard is **live-source only**. It does not render seeded examples or local sample catalog rows when upstream discovery is unavailable. Persisted `ContentItem`/`ContentAvailability` data supports saved titles and provider-aware user state; it is not substituted for live home-page discovery.

aitv does not invent provider URLs. A provider-specific/direct button is shown only when an upstream source supplies a legitimate destination. TMDB regional watch context can identify services and access types, but its regional watch-options URL is kept as a regional options destination rather than guessed into provider deep links.

Missing upstream fields stay visibly unavailable instead of being fabricated. Availability varies by title and region.

## Project structure

```text
aitv/
├── content/         # Catalog persistence, provider detection, and live-source adapters
├── core/            # Dashboard, profile/preferences, registration, and tests
├── notifications/   # Favorite release detection, inbox, email state, and worker tests
├── streamhub/       # Django project package (settings, URLs, WSGI)
├── watchlist/       # Per-user Watchlist/Favorite page and controls
├── static/          # Site CSS and JavaScript
├── templates/       # Shared, account, content, notification, and watchlist templates
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

`streamhub/` is the historical Django project-package name; the application/product is **aitv**.

## Quick local testing with Docker

```bash
git clone https://github.com/drakeg/aitv.git
cd aitv
cp .env.example .env
docker compose up -d --build
docker compose logs -f web
```

The web container runs migrations and starts Django. It does **not** load demo content. The default site is `http://127.0.0.1:8000/`.

To use another host port, set for example:

```dotenv
APP_PORT=8007
```

The source tree is bind-mounted, so normal Python/template/static edits are picked up by Django's development reloader. Rebuild when dependencies or the Dockerfile change.

Useful commands:

```bash
docker compose up -d --build
docker compose logs -f web
docker compose run --rm web python manage.py check
docker compose run --rm web python manage.py test
docker compose run --rm web python manage.py createsuperuser
docker compose down
```

### Persistent SQLite data

Compose stores the development database in the named `aitv_data` volume at `/data/db.sqlite3`. This avoids the common SQLite locking problems caused by using the bind-mounted source tree as the active database location.

**Do not use `docker compose down -v` unless you intentionally want to delete the persisted local database volume.** Normal `docker compose down` keeps it.

`SQLITE_DB_PATH` and `SQLITE_TIMEOUT_SECONDS` can override the defaults when needed.

## Accounts and personalization

Registration signs a new user in immediately. Existing users have login/logout, Profile, Watchlist, Favorites, and notifications.

Discovery tuning is account-specific. The public/default experience remains neutral: one user's category, content-mix, region, or provider choices never change another account. News and Soap/Soap Opera are ordinary selectable categories rather than globally suppressed categories.

Preferred streaming services affect ordering only. If TMDB reports legitimate regional providers, a signed-in viewer's selected services are moved ahead in each title's provider choices. As live provider context loads, matching non-favorite titles are also promoted ahead of other non-favorites and show an `On <provider>` badge. Favorites remain the highest-priority account signal, and all nonmatching titles remain available.

## Live source workflow

### TVmaze

TVmaze supplies scheduled TV plus show/network or web-channel, episode, runtime, airtime, genres, and official destinations where available. A card can remain useful as schedule metadata even when TVmaze does not publish a direct show URL. aitv can lazily resolve an exact TVmaze title to a canonical TMDB title for regional provider context and saved/Favorite state.

### Internet Archive

The Internet Archive adapter pulls current public movie records from its search endpoint and links to playable item pages supplied by the source.

### TMDB

TMDB supplies movie/TV discovery, metadata, canonical IDs, and regional watch-provider context. Configure either credential; both are not required:

```dotenv
TMDB_API_KEY=your_key_here
# or
TMDB_READ_ACCESS_TOKEN=your_read_token_here
```

Provider context is ordered Free → Free with ads → Subscription → Rent → Buy, then adjusted within that legitimate result set for a signed-in viewer's preferred services. Cards show the first two providers compactly and allow the remaining provider names/access types to be expanded in place.

TMDB failures or missing credentials do not prevent other live sources from loading.

## Favorite release notifications

Favorites are distinct from ordinary Watchlist saves. The release checker looks for newly reported TV release state for eligible saved TMDB TV Favorites, creates in-app notifications, and can optionally send email. The authenticated notification inbox displays 25 newest-first notifications per page while the navigation badge continues to reflect the account's total unread count. Pagination includes direct page-number links with an elided range for longer histories, alongside Previous/Next controls. Marking one notification or all notifications read keeps the viewer on the current inbox page; both return targets use the same same-site URL validation before redirecting.

Run a one-time check manually with:

```bash
docker compose run --rm web python manage.py check_release_notifications
```

For recurring checks in Docker, enable the opt-in profile:

```bash
docker compose --profile notifications up -d --build
```

The worker uses the same image, `.env`, and `aitv_data` SQLite volume. It runs a check, waits `RELEASE_CHECK_INTERVAL_SECONDS`, and repeats. The default is 3600 seconds. Empty, non-numeric, or zero interval values fall back to 3600. A failed individual check is logged and retried on the next interval; the worker also uses `restart: unless-stopped`.

The worker is **not** started by ordinary `docker compose up` unless the `notifications` profile is selected.

SMTP is optional. Without SMTP, recurring checks can still create in-app notifications.

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `APP_PORT` | `8000` | Host port exposed by Docker Compose. |
| `DJANGO_SECRET_KEY` | development fallback in Compose | Django signing secret; set a real secret outside local development. |
| `DJANGO_DEBUG` | `true` | Enables/disables Django debug mode. |
| `DJANGO_ALLOWED_HOSTS` | local hosts in Compose | Comma-separated accepted hostnames. |
| `SQLITE_DB_PATH` | `/data/db.sqlite3` in Compose | Active SQLite database path. |
| `SQLITE_TIMEOUT_SECONDS` | `30` | SQLite busy timeout. |
| `TMDB_API_KEY` | empty | Optional TMDB v3 API-key authentication. |
| `TMDB_READ_ACCESS_TOKEN` | empty | Optional TMDB Bearer-token authentication; preferred when set. |
| `TMDB_TIMEOUT_SECONDS` | `5` | TMDB request timeout fallback. |
| `SOURCE_TIMEOUT_SECONDS` | `5` | Shared upstream-source timeout. |
| `RELEASE_CHECK_INTERVAL_SECONDS` | `3600` | Positive whole-number interval for the opt-in notification worker. |
| `SMTP_HOST` | empty | SMTP server; empty disables release-notification email. |
| `SMTP_PORT` | `587` | SMTP port. |
| `SMTP_USERNAME` | empty | Optional SMTP username. |
| `SMTP_PASSWORD` | empty | Optional SMTP password. |
| `SMTP_USE_TLS` | `true` | Enable SMTP TLS. |
| `DEFAULT_FROM_EMAIL` | empty | Sender address for notification email. |

## Standard local setup without Docker

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

### Definition of done

Feature and maintenance work is expected to keep implementation, tests, and documentation synchronized. Behavior changes should include regression coverage at the most appropriate layer and update README/product/operations documentation when user-visible behavior, configuration, architecture, or operating procedures change. CI must pass before a sprint PR is treated as ready. The full sprint workflow and maintenance-review checklist live in `docs/agile.md`. Repository coding rules live in `docs/coding-standards.md`, and the durable sprint history is maintained in `docs/sprints.md`.

## Architecture notes

`core.views.home` assembles live discovery from TVmaze, Internet Archive, and TMDB. Server-side ranking accounts for direct-watch usefulness, user content mix, categories, and known Favorite state. Browser-side enrichment adds TMDB context to eligible TVmaze cards near the viewport and can immediately synchronize Watchlist/Favorite state and provider choices without a page refresh.

The Docker path remains development-focused: Django's development server, bind-mounted source, persistent SQLite, and an optional lightweight notification worker. Production server/database/static serving/security/health-check deployment remains separate work.

## Security and provider authentication

Do not commit real API keys, SMTP passwords, or production secrets. `.env` is ignored by Git; use appropriate secret storage for deployed environments. State-changing account/catalog/Watchlist/Favorite actions use POST requests with Django CSRF protection.

aitv does not bypass provider authentication or DRM and does not store/replay raw streaming-provider passwords. Future provider-account connections should use provider-supported OAuth/token/session mechanisms where available.

## Status

aitv now centers live TV/movie discovery, truthful provider/network visibility, recognized provider watch destinations supplied by live sources (visibly labeled `Direct watch`; unrecognized official sites remain details-only; recognized coverage includes The Roku Channel and both Prime Video's native domain and scoped Amazon video paths), compact regional provider choices whose TMDB links are labeled as provider discovery rather than direct playback, account-specific personalization, Watchlist/Favorites, and optional recurring Favorite release notifications.
