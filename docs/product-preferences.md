# Personalized discovery

aitv should prioritize watchable content while allowing each viewer to decide what appears in discovery.

## Default behavior

- The public/default experience does not globally suppress a genre or program type. News is treated like any other category.
- Signed-in users can save their own preferred discovery categories to their account.
- Preferences can include or exclude Comedy, Crime, Drama, News, Reality, Science Fiction, Action, Documentary, Soap/Soap Opera, and other supported genres independently.
- A user's choices affect live and trending discovery rows, not another user's results.
- Common upstream category wording is normalized so source differences do not bypass preferences. This includes Soap/Soap Opera, Science Fiction/Science-Fiction/Sci-Fi & Fantasy, and Action/Adventure/Action & Adventure.
- For customized accounts, TV rows are ranked by how many selected categories each show matches. Upstream order is preserved for ties, and the neutral/default experience keeps the source's original ordering.
- Personalization applies consistently to On TV Today, Trending TV Today, TV On the Air, and Popular TV.
- Live-source cards expose genre and network/service information whenever the upstream source provides it.
- Provider/watch actions remain primary; metadata destinations remain secondary.

## Profile data, favorites, and notifications

- Profile stores optional first name, last name, and email address on the user's Django account.
- Regional availability and discovery-category settings remain account-specific.
- Watchlist and Favorite are separate concepts: saving a title means "watch later"; marking it Favorite means the user wants it prioritized and eligible for release alerts.
- Users can opt in globally to release alerts, but only Favorite saved titles are checked. Opt-in requires a saved email address and defaults off.
- `python manage.py check_release_notifications` checks opted-in Favorite titles for newly aired episodes on supported sources.
- The first successful check establishes a baseline and does not generate historical notifications. Removing Favorite status clears that baseline so re-favoriting starts cleanly rather than producing catch-up spam.
- The first release detector supports TMDB-backed TV titles. Unsupported sources are skipped rather than guessed.
- Email delivery is optional and occurs only when SMTP settings are explicitly configured. Without SMTP configuration, the in-app notification workflow still works and no outbound email is attempted.
- Notification read actions are per-user and POST-only.

Personalization applies to discovery results only. A user's saved catalog is never silently deleted or hidden because of discovery preferences.
