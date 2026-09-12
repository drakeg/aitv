# Content refresh and TV discovery

aitv builds the discovery dashboard from live upstream requests each time the home page is loaded. The app does not keep a long-lived cache of the home-page discovery rows.

## Source behavior

- **TVmaze — On TV Today:** fetched on each page load for the selected account region. Up to 100 unique scheduled shows are considered before account discovery preferences are applied. Shows are retained even when TVmaze does not publish an `officialSite`, so real network, episode, runtime, airtime, genre, and image data are not discarded. When an official destination is unavailable, aitv labels the card accordingly and exposes TVmaze source details instead of inventing a watch link. Metadata-only TVmaze cards that are actually visible are lazily matched to TMDB by exact normalized title as they approach the viewport. If TMDB has concrete providers in the selected region, aitv adds those provider labels and a **See regional watch options** action; no provider URL is guessed. Matching/provider results are cached for 30 minutes so scrolling does not repeatedly hit TMDB. Cards with a real source-supplied watch destination remain ranked ahead of metadata-only cards; personalized genre relevance still orders titles within the same actionability group.
- **TMDB — Trending TV Today:** fetched from TMDB's daily TV trending feed on each page load. The ranking is controlled by TMDB and may remain similar across multiple visits during the same day.
- **TMDB — TV On the Air:** fetched on each page load to broaden the current-series pool beyond trending titles.
- **TMDB — Popular TV:** fetched on each page load as an additional discovery pool.
- **TMDB — Trending Movies:** fetched from TMDB's weekly movie trending feed on each page load.
- **Internet Archive — Watch Free Now:** fetched on each page load, sorted by downloads, so highly downloaded titles may remain stable for long periods.

TMDB TV rows are deduplicated across Trending TV, TV On the Air, and Popular TV so the same TMDB series is not repeated in multiple TV discovery rows. Each of those rows can display up to 20 titles before regional provider validation in the browser removes titles that are not available in the user's selected region.

TMDB per-title watch-provider enrichment is cached separately for 30 minutes by region. TVmaze-to-TMDB exact-title provider resolution uses the same 30-minute cache window. These caches affect provider/network/runtime enrichment, not which discovery lists are requested.
