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

## Refresh operations

**Implemented in Sprint 64:** normalized EPG persistence now has a supported `refresh_epg` management command and an opt-in Docker `epg` worker. Operators can refresh one or multiple configured regions, control expired-airing retention, and choose the recurring refresh interval through `.env`. Worker failures are surfaced and retried on the next interval; ordinary `docker compose up` does not enable recurring EPG refreshes.

## Airing-specific destinations

**Implemented in Sprint 66:** trusted provider URLs supplied by the TVmaze schedule path are normalized into source-owned AiringDestination records rather than ChannelDestination records. Each refresh revalidates the URL through the existing provider detector and removes a stale source destination if upstream no longer supplies a trusted URL. The Live TV guide prefers the current airing's destination over a broader channel destination, while future/other airings remain unaffected.

## Operator destination management

**Implemented in Sprint 65:** Django admin provides an operator surface for the normalized EPG domain. Source-owned Channels, Programs, and Airings plus account-owned Channel Favorites are inspect-only for add/delete operations. Existing Channels expose editable ChannelDestination rows so an operator can deliberately record a provider, URL, access type, destination type, and provenance source without modifying schedule identities. Playable destinations entered through this surface must use HTTP(S), and the guide still renders Watch actions only for explicit direct/tuner destination types.
