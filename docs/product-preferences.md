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
- If a viewer saves discovery preferences with no categories selected, aitv treats that as a request to show all categories rather than creating an empty customized catalog. The Profile page also provides an explicit **Show all categories** reset action.
- Resetting discovery categories changes only the category filter; region, strict regional availability, provider preferences, content-mix ordering, and notification preferences remain intact.
- Each account can choose a dashboard content mix: Balanced, TV first, or Movies first. Balanced is the neutral default and interleaves movie rows with TV discovery; TV first keeps all TV discovery ahead of movie rows; Movies first does the reverse.
- The same content-mix ordering applies to live search/browse results.
- Content-mix ordering is account-specific and does not globally change the public/default experience.
- Each signed-in account can optionally select streaming services it uses. When TMDB supplies legitimate regional provider choices, aitv presents selected services first and progressively moves titles available on those services ahead of other non-favorite titles as live provider context loads. A confirmed match is labeled `On <provider>` on the card so the reason for the personalized promotion is visible. When that preferred service is also the first reported regional watch choice, the provider-listing button names the service and access type (for example, subscription) using `Find … option` wording rather than implying a direct provider deep link. Live source-supplied destinations are separately labeled `Direct watch`. Favorites remain the highest-priority account signal.
- Common profile labels are normalized only for matching against upstream provider names—for example, `Amazon Prime Video` matches `Prime Video`, `Disney Plus` matches `Disney+`, `Paramount Plus` matches `Paramount+`, `Peacock Premium` matches `Peacock`, and `Tubi TV` matches `Tubi`. The saved profile labels remain unchanged.\n- Provider preferences do not hide titles, fabricate deep links, change regional availability truth, or alter another account. With no selected services, title and provider ordering remain neutral/upstream-driven.
- When strict regional availability is enabled, a TMDB title must have at least one concrete provider row in the selected region. A generic TMDB/JustWatch landing link by itself does not count as regional availability.
- Strict regional availability also applies to TVmaze schedule results: metadata-only cards without a source-supplied watch destination are validated through the safe TVmaze-to-TMDB enrichment path, while broader schedule discovery remains available to non-strict accounts.
- The same strict live-source filtering is applied to search/browse results.
- If regional validation removes every TMDB card from a discovery row, the UI shows an explicit regional empty state instead of leaving a blank row.
- Live-source cards expose genre and network/service information whenever the upstream source provides it.
- Provider/watch actions remain primary; metadata destinations remain secondary.

## Profile data, favorites, and notifications

- Profile stores optional first name, last name, and email address on the user's Django account.
- Regional availability, provider preferences, content-mix, and discovery-category settings remain account-specific.
- Watchlist and Favorite are separate concepts: saving a title means "watch later"; marking it Favorite means the user wants it prioritized and eligible for release alerts.
- Signed-in viewers see known Favorite titles first within each discovery row. This is a stable promotion: non-favorite titles retain their existing source/personalization order, saved-but-not-favorite titles are not promoted, and the public/anonymous experience is unchanged.
- Favorite / Unfavorite changes made from discovery update the current page immediately: every visible card for the same saved title is synchronized, affected rows are regrouped with Favorites first, and Watchlist removal demotes a formerly Favorite card without requiring a reload.
- Because live search/browse uses the same already-ranked source groups, Favorite promotion is preserved there without overriding the viewer's TV-first/Movies-first content-mix choice.
- Saved TMDB discovery cards expose Favorite / Unfavorite directly on the discovery page. When a new TMDB title is saved asynchronously, the Favorite control is added immediately without requiring a page reload or a trip to the Watchlist page.
- TVmaze **On TV Today** cards can also expose Save / Favorite controls after aitv safely resolves a canonical TMDB identity; the source-supplied network Watch action remains primary.
- Users can opt in globally to release alerts, but only Favorite saved titles are checked. Opt-in requires a saved email address and defaults off.
- `python manage.py check_release_notifications` checks opted-in Favorite titles for newly aired episodes on supported sources.
- The first successful check establishes a baseline and does not generate historical notifications. Removing Favorite status clears that baseline so re-favoriting starts cleanly rather than producing catch-up spam.
- The first release detector supports TMDB-backed TV titles. Unsupported sources are skipped rather than guessed.
- Email delivery is optional and occurs only when SMTP settings are explicitly configured. Without SMTP configuration, the in-app notification workflow still works and no outbound email is attempted.
- Release notifications persist a successful email-delivery timestamp independently from the release baseline. If SMTP raises a transient error, the in-app notification remains available and a later `check_release_notifications` run retries that same unsent email without creating a duplicate notification.
- The authenticated notification inbox is newest-first and paginated at 25 notifications per page; the navigation badge remains the total unread count across pages. Longer histories expose direct, elided page-number navigation in addition to Previous/Next controls.
- Notification read actions are per-user and POST-only. Marking an individual notification or all notifications read returns to the current inbox page when the submitted return URL is same-site; unsafe/external return targets fall back to the inbox.

Personalization applies to discovery results only. A user's saved catalog is never silently deleted or hidden because of discovery preferences.
