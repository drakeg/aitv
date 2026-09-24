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
- **Viewer state**: Favorite channels/programs and provider preferences, scoped per account.

Airing data and playback destinations must not be conflated. Knowing that a program airs on a channel does not prove that aitv has a playable URL for it.

## Source trust boundary

- Every channel, schedule row, and destination records its source/provenance.
- Direct playback is exposed only when an authoritative source supplies a destination or an explicit trusted adapter establishes one.
- Generic websites, arbitrary IPTV URLs, unknown M3U playlists, and scraped stream URLs are not promoted to trusted playback.
- Missing playback remains a useful metadata-only guide entry.
- Region and access requirements remain visible rather than being bypassed.
- aitv does not bypass DRM or provider authentication and does not rebroadcast commercial channels itself.

## Initial implementation path

1. Introduce normalized Channel/Program/Airing concepts without replacing existing discovery. **Implemented in Sprint 57:** persisted source identities and region-aware channels, reusable programs, timed airings, duplicate guards, and an end-after-start constraint. Playback URLs intentionally remain outside these schedule models.
2. Normalize existing trustworthy schedule data into the EPG persistence layer. **Implemented in Sprint 58 for TVmaze:** stable source identities are upserted into Channel/Program/Airing records, repeated refreshes are idempotent, malformed identity/time rows are skipped, and only expired TVmaze airings are cleaned up.\n3. Build a Live TV guide route and now/next presentation from the normalized schedule data.
4. Add per-user channel Favorites and filtering.
5. Add additional legitimate channel/schedule adapters one source at a time with contract tests.
6. Add supported provider/session or user-owned tuner integrations separately from schedule ingestion.
7. Add search across channels/programs and preferred-destination ranking.

Each source integration must define its provenance, region semantics, access type, refresh behavior, failure behavior, and whether its URL is metadata, provider discovery, or direct playback.
