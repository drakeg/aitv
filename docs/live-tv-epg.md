# Live TV / EPG architecture

aitv's Live TV direction is a unified electronic program guide (EPG) across legitimate sources. The product should provide the convenience of a large channel guide without becoming an unlicensed retransmission service.

## Product goal

A viewer should be able to browse a familiar channel/program grid, search channels and programs, Favorite channels, see what is on now/next, and launch the best legitimate viewing destination available to that account and region.

The guide may combine:

- free/ad-supported streaming channels from supported sources;
- broadcaster/network destinations supplied by authoritative sources;
- subscription/provider destinations;
- user-owned OTA/network-tuner sources where a future supported integration can establish the local stream;
- metadata-only channels/programs when playback is unavailable.

## Core entities

Future implementation should separate:

- **Channel**: stable channel identity, display name/logo, region, categories, source provenance.
- **Program**: title and descriptive metadata independent of a particular airing.
- **Airing**: channel + start/end time + program.
- **Channel destination**: provider/source URL plus access type and provenance.
- **Airing destination**: source-supplied episode/show playback URL scoped to one scheduled airing.
- **Viewer state**: Favorite channels/programs and provider preferences, scoped per account.

Airing data and playback destinations must not be conflated. Knowing that a program airs on a channel does not prove that aitv has a playable URL for it. Likewise, a show/episode URL supplied for one airing must not be promoted to a channel-wide destination.

## Source trust boundary

- Every channel, schedule row, and destination records its source/provenance.
- Direct playback is exposed only when an authoritative source supplies a destination or an explicit trusted adapter establishes one.
- Generic websites, arbitrary IPTV URLs, unknown M3U playlists, and scraped stream URLs are not promoted to trusted playback.
- Missing playback remains a useful metadata-only guide entry.
- Region and access requirements remain visible rather than being bypassed.
- aitv does not bypass DRM or provider authentication and does not rebroadcast commercial channels itself.

## Initial implementation path

1. Introduce normalized Channel/Program/Airing concepts without replacing existing discovery. **Implemented in Sprint 57:** persisted source identities and region-aware channels, reusable programs, timed airings, duplicate guards, and an end-after-start constraint. Playback URLs intentionally remain outside these schedule models.
2. Normalize existing trustworthy schedule data into the EPG persistence layer. **Implemented in Sprint 58 for TVmaze:** stable source identities are upserted into Channel/Program/Airing records, repeated refreshes are idempotent, malformed identity/time rows are skipped, and only expired TVmaze airings are cleaned up.
3. Build a Live TV guide route and now/next presentation from the normalized schedule data. **Implemented in Sprint 59:** `/live-tv/` reads normalized EPG persistence, groups current/next programming by channel, respects the signed-in account region, and does not expose playback actions from schedule data alone.
4. Add per-user channel Favorites and filtering. **Implemented in Sprint 60:** signed-in viewers can persist account-scoped channel Favorites, toggle them from the guide, and filter the guide to only their own Favorite channels. Favorite state remains separate from schedule and playback provenance.
5. Add additional legitimate channel/schedule adapters one source at a time with contract tests. **Adapter foundation implemented in Sprint 61:** schedule sources now normalize into a shared airing contract before persistence, TVmaze uses that contract, provenance/cleanup remain source-scoped, and contract tests cover malformed data and source isolation. A second external source still requires an authoritative supported API rather than an unofficial feed.
6. Add supported provider/session or user-owned tuner integrations separately from schedule ingestion. **Destination foundation implemented in Sprint 62:** trusted ChannelDestination records now persist provider/source URL, access type, destination semantics, and provenance separately from Airing data. The guide renders Watch actions only for destinations explicitly classified as direct playback or a user-owned tuner; provider-discovery/details URLs remain non-playback metadata.
7. Add search across channels/programs and preferred-destination ranking. **Implemented in Sprint 63:** the Live TV guide can search normalized channel names and upcoming program titles while preserving now/next context, Favorites filtering can be combined with search, and signed-in viewers' preferred providers rank otherwise-legitimate playable channel destinations without fabricating availability.

Each source integration must define its provenance, region semantics, access type, refresh behavior, failure behavior, and whether its URL is metadata, provider discovery, or direct playback.

## Discovery deduplication versus EPG completeness

**Implemented in Sprint 78:** TVmaze home discovery continues to collapse repeated same-day airings of the same show into one discovery card. The normalized EPG refresh uses the same source fetcher in full-schedule mode instead, preserving every distinct TVmaze episode/schedule identity so back-to-back or repeated airings are not silently dropped before persistence.

## Authoritative schedule timestamps

**Sprint 67:** TVmaze's episode `airstamp` supplies a dated, timezone-aware instant. EPG normalization preserves that timestamp, including post-midnight broadcasts and offsets; a bare `airtime` is no longer promoted to a guessed server-date airing. Missing, malformed, or timezone-naive airstamps are skipped rather than fabricating current/next guide timing. The existing Live TV home cards can still show their source-supplied airtime label.

## Refresh operations

**Implemented in Sprint 64:** normalized EPG persistence now has a supported `refresh_epg` management command and an opt-in Docker `epg` worker. Operators can refresh one or multiple configured regions, control expired-airing retention, and choose the recurring refresh interval through `.env`. Worker failures are surfaced and retried on the next interval; ordinary `docker compose up` does not enable recurring EPG refreshes.

## Complete-snapshot reconciliation

**Implemented in Sprint 79:** schedule adapters can explicitly declare that a successful refresh is a complete regional snapshot. TVmaze does so. For those adapters, current/future source airings missing from the latest successful snapshot are removed for that source and region, preventing cancelled or withdrawn schedule rows from lingering in the guide. Recent expired airings are still retained according to `EPG_RETENTION_HOURS`, and adapters that do not declare complete-snapshot semantics are never reconciled this way.

## Complete-snapshot fetch completeness

**Implemented in Sprint 80:** adapters that declare complete-snapshot semantics are fetched without the normal row cap before reconciliation. TVmaze therefore cannot be treated as a complete regional snapshot after an application-side truncation. Partial adapters retain the bounded fetch contract and are not reconciled as complete snapshots.

## Malformed snapshot protection

**Implemented in Sprint 81:** an authoritative source returning a genuinely empty schedule remains a successful empty snapshot. However, if TVmaze returns a non-empty schedule and every row fails normalization, the refresh fails closed before reconciliation. The previous current/future schedule remains intact, and normal refresh-failure observability records the failed attempt instead of treating malformed data as an authoritative empty schedule.

## Partial snapshot protection

**Implemented in Sprint 82:** complete TVmaze snapshots now require every returned source row to normalize successfully. If even one row is malformed, the refresh fails before persistence and reconciliation, so valid rows from that same partial snapshot are not applied and existing current/future guide data is preserved. This extends Sprint 81's zero-valid-row protection to mixed valid/invalid responses.

## Complete snapshot identity requirements

**Implemented in Sprint 83:** every TVmaze row in a complete snapshot must carry stable airing/episode, channel, and program/show identities before the snapshot is eligible for persistence or reconciliation. Identity-incomplete rows fail the refresh closed, preventing later persistence-layer skipping from silently turning a complete snapshot into a partial authoritative one.

## Duplicate airing consistency

**Implemented in Sprint 84:** a complete TVmaze snapshot may not assign one airing/episode ID to conflicting channel, program, or normalized start/end timing. Conflicting duplicates fail the refresh closed before persistence or reconciliation. Exact duplicate rows with the same identity and timing are collapsed so one upstream duplication does not double-count or repeatedly rewrite the same normalized airing.

## Refresh freshness observability

**Implemented in Sprint 68:** each completed TVmaze refresh records source, region, completion time, and normalized airing count. The Live TV guide displays the refresh age and warns when the most recent completed refresh exceeds `EPG_STALE_AFTER_SECONDS` (default 7200). Refresh state is read-only in Django admin, so a stopped worker can be distinguished from ordinary schedule gaps.

## Source failure versus empty schedule

**Sprint 70:** interactive TVmaze home discovery remains fail-soft, but the scheduled EPG refresh invokes strict TVmaze fetching. Transport, HTTP, JSON, or unexpected payload failures raise a sanitized source error, allowing the refresh command to record failure while preserving the previous successful schedule state. A valid empty source schedule remains a successful zero-airing refresh. Source exception text, response bodies, and credentials are not copied into the persisted error summary.

## Refresh failure observability

**Implemented in Sprint 69:** refresh state now records the latest attempt time, success/failure status, and an operator-visible error summary without overwriting the prior successful refresh timestamp or airing count. Multi-region refreshes continue healthy regions before returning failure for failed regions. The public guide shows a generic failure warning but never exposes stored exception details.

## Operational health endpoints

**Implemented in Sprint 71:** `/health/live/` verifies the Django/database path and is suitable for container liveness. `/health/ready/` verifies the same database path plus each configured `EPG_REGIONS` refresh state; missing, failed, or older-than-`EPG_STALE_AFTER_SECONDS` regions return HTTP 503 with sanitized structured status. Docker Compose uses liveness only, so an upstream schedule outage does not trigger a restart loop while external monitoring can still alert on degraded readiness.

## Shared EPG health policy

**Implemented in Sprint 72:** configured-region parsing, stale-threshold normalization, and `missing`/`failed`/`stale`/`ok` evaluation live in one shared policy module. Both the Live TV guide and `/health/ready/` consume that policy, preventing user-facing freshness warnings from drifting away from operational readiness semantics.

## Missing refresh-state visibility

**Implemented in Sprint 73:** the Live TV guide now surfaces the shared `missing` EPG health state as a warning instead of silently presenting schedule rows with no tracked refresh history. This keeps guide messaging aligned with `/health/ready/`, which already treats missing refresh state as degraded readiness.

## Now / Next / Later guide context

**Implemented in Sprint 86:** each Live TV channel row now shows the current airing plus the next two future normalized airings as **Now**, **Next**, and **Later**. The guide remains schedule-only unless an explicit trusted destination is present, and the existing responsive layout stacks the added program slot on narrow screens.

## Visible guide search scope

**Implemented in Sprint 87:** Live TV search now matches channel names plus only the program titles visible in the compact **Now / Next / Later** row. Programs farther in the future no longer make a channel appear without showing the matching title, keeping search results explainable and aligned with the visible guide context.

## Live TV category filtering

**Implemented in Sprint 74:** the Live TV guide can filter by normalized channel categories already stored with EPG channels. Category filtering composes with channel/program search and Favorites-only mode, and favorite toggle actions preserve the active search/category filter state.

## Favorite-first guide ordering

**Implemented in Sprint 75:** signed-in viewers see Favorite channels before non-Favorites in the normal Live TV guide, with alphabetical ordering preserved inside each group. Anonymous guide ordering remains alphabetical, and Favorites-only mode remains unchanged.

## Playable-now filtering

**Implemented in Sprint 85:** the Live TV guide can restrict results to channels with an explicit trusted playback destination available for the current view. A channel qualifies when its current airing has a trusted `AiringDestination` or the channel has a playable direct/tuner `ChannelDestination`. Future-airing destinations, metadata/details URLs, and schedule presence alone do not qualify. The filter composes with search, category, and account-scoped Favorites state.

## Airing-specific destinations

**Implemented in Sprint 66:** trusted provider URLs supplied by the TVmaze schedule path are normalized into source-owned AiringDestination records rather than ChannelDestination records. Each refresh revalidates the URL through the existing provider detector and removes a stale source destination if upstream no longer supplies a trusted URL. The Live TV guide prefers the current airing's destination over a broader channel destination, while future/other airings remain unaffected.

## Airing destination ranking

**Implemented in Sprint 76:** when the current airing has multiple trusted destinations, episode scope ranks ahead of show scope. Within the same scope, a signed-in viewer's preferred providers rank ahead of other legitimate destinations using the same provider-alias normalization already used for channel destinations. Provider preference never promotes a broader show destination over a matching episode-specific destination.

## Airing destination scope visibility

**Implemented in Sprint 77:** the Live TV guide visibly labels the selected AiringDestination as episode-specific or show-level. ChannelDestination actions remain unlabeled by airing scope, avoiding any implication that a channel-wide destination is tied to one episode or show. This is presentation-only and does not change destination selection or trust rules.

## Operator destination management

**Implemented in Sprint 65:** Django admin provides an operator surface for the normalized EPG domain. Source-owned Channels, Programs, and Airings plus account-owned Channel Favorites are inspect-only for add/delete operations. Existing Channels expose editable ChannelDestination rows so an operator can deliberately record a provider, URL, access type, destination type, and provenance source without modifying schedule identities. Playable destinations entered through this surface must use HTTP(S), and the guide still renders Watch actions only for explicit direct/tuner destination types.
