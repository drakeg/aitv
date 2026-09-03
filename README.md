# StreamHub

StreamHub is a Django application for aggregating legitimate streaming and television discovery into a watch-first interface. The project favors direct provider destinations over metadata-only pages and supports local Docker development.

## Product direction

- Use TMDB for metadata and discovery, not as the preferred viewing destination.
- Prefer legitimate direct provider links where available.
- Show the network/service, episode context, runtime, title, and watch destination prominently.
- Support multiple providers for a title.
- Keep user watchlists and discovery preferences account-specific.
- Do not bypass authentication, DRM, subscriptions, or provider access controls.

## Personalized discovery

Signed-in viewers can tune discovery by selecting the genres and program types they want to see. Preferences are stored per account and apply to live/trending discovery only. The public/default experience does not globally suppress News or any other category, so another user can choose a completely different mix without affecting anyone else.

Examples include Comedy, Crime, Drama, Action, Reality, News, Documentary, Animation, Horror, Romance, Sci-Fi & Fantasy, Talk, Sports, and more. Saved/local catalog items are not removed or hidden by discovery preferences.

## Local Docker quick start

1. Copy `.env.example` to `.env` and fill in any optional service credentials you want to use.
2. Start the application with `docker compose up --build`.
3. Open `http://localhost:${APP_PORT:-8000}`.

The listen port is controlled with `APP_PORT`.

## Environment variables

```env
APP_PORT=8000
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
TMDB_API_KEY=
TMDB_READ_ACCESS_TOKEN=
TMDB_TIMEOUT_SECONDS=5
SOURCE_TIMEOUT_SECONDS=5
LOAD_DEMO_CONTENT=true
```

`TMDB_READ_ACCESS_TOKEN` is preferred when both TMDB credential styles are configured. `SOURCE_TIMEOUT_SECONDS` controls live-source request timeouts and falls back to the TMDB timeout when omitted.

## Live sources

Current live discovery includes today's US TV schedule from TVmaze and playable public movie records from the Internet Archive. Source adapters fail closed so an upstream outage does not prevent the rest of the application from rendering.

## Authentication and watchlists

Users can register, sign in, save titles to their watchlist, and remove titles without a full-page refresh. Provider authentication requirements are displayed rather than bypassed.

## Development

Run Django checks/tests locally with the project environment or Docker. CI should remain fast and focused on Django checks, tests, and Docker/build validation.
