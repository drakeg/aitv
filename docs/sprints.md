# Sprint ledger

This ledger is the durable project record for sprint-sized development. Git history and pull requests remain the detailed source of truth.

## Current era

| Sprint | PR | Goal / outcome |
| --- | --- | --- |
| 40 | #64 | Provider-aware title ranking. |
| 41 | #65 | Visible preferred-provider match feedback. |
| 42 | #66 | Quality/docs/tests audit and Agile definition of done. |
| 43 | #67 | Notification inbox pagination. |
| 44 | #68 | Page-preserving individual notification read action. |
| 45 | #69 | Page-preserving mark-all-read and shared safe redirects. |
| 46 | #70 | Elided notification page navigation. |
| 47 | #71 | Preferred-provider watch action labels. |
| 48 | #72 | Separate direct-watch destinations from provider discovery/listing links. |
| 49 | #73 | Validate TVmaze direct-watch destinations. |
| 50 | #74 | Expand trusted direct-watch provider coverage. |
| 51 | #75 | Fix current-page-aware notification pagination. |
| 52 | #76 | Prefer source-supplied episode-specific direct-watch links. |
| 53 | #77 | Path-scope ABC/CBS/NBC/FOX direct-watch recognition. |
| 54 | #78 | Complete network path scoping for PBS and The CW. |
| 55 | #79 | Normalize provider-preference aliases against canonical upstream names. |
| 56 | #80 | Establish repository-wide coding/sprint standards and Live TV/EPG architecture boundaries. |
| 57 | #81 | Add the normalized Channel / Program / Airing persistence foundation and schedule invariants. |
| 58 | #82 | Normalize trustworthy TVmaze schedule data into idempotent EPG persistence. |
| 59 | #83 | Add the first region-aware Live TV now/next guide backed by normalized EPG data. |
| 60 | #84 | Add per-user Live TV channel Favorites and Favorites-only guide filtering. |

## Earlier development

Sprints 1-39 established the Django foundation, live-source ingestion, accounts, Watchlist/Favorites, provider-first discovery, regional availability, per-user discovery preferences, release notifications, Docker operation, provider enrichment, strict regional filtering, Favorite-first ranking, and reliability hardening. Earlier PR history remains available in GitHub; future sprints should be entered here as they are opened rather than reconstructed from chat history.

## Maintenance rule

Every merged sprint should leave this ledger accurate. If a sprint is split, superseded, or closed without merge, record that outcome instead of silently renumbering history.
