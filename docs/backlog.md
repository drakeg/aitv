# Product backlog

This is the repository-owned backlog for aitv. It records the next likely sprint targets, important deferred work, and maintenance debt so planning does not depend on chat history.

Priorities can change when local testing, CI, security review, source behavior, or user feedback exposes something more important. When that happens, update this file and the planned queue in `docs/sprints.md` together.

## Near-term sprint queue

### Commercial validation — SMB hospitality pilot

Validate the guest-entertainment-guide hypothesis before building substantial commercial-only features.

Acceptance direction:
- Prepare a demo suitable for an independent hospitality operator.
- Interview at least 10 qualified operators about entertainment-discovery/support pain and current workarounds.
- Ask for a paid pilot rather than treating positive feedback as willingness to pay.
- Record objections and feature requests as evidence, not assumed demand.
- Treat the pricing ideas in `docs/commercialization.md` as hypotheses until a customer agrees to pay.

### Sprint 123 — Next legitimate EPG/source adapter

Evaluate and add the next schedule source only if it can satisfy the existing provenance and trust contract.

Acceptance direction:
- Document region semantics, refresh completeness, stable identities, timestamps, access type, and destination meaning.
- Treat schedule metadata and playback destinations separately.
- Add adapter contract tests and fail closed when an authoritative snapshot is incomplete or ambiguous.
- No scraped streams, mystery playlists, guessed playback URLs, DRM bypass, or credential replay.

### Sprint 124 — Production-readiness hardening

Move beyond the development-only Docker path where appropriate.

Acceptance direction:
- Define the supported production serving model for Django, static assets, secrets, database, health checks, and deployment configuration.
- Keep local Docker development simple and separate from production concerns.
- Document upgrade/rollback and data-persistence expectations before declaring production readiness.

## Ongoing maintenance backlog

These items are continuous rather than assigned to one fixed sprint:

- Keep dependencies on supported secure versions and review Renovate output.
- Keep Docker Compose, Django checks, tests, and build commands free of avoidable warnings.
- Keep README, focused architecture/product docs, sprint history, and this backlog synchronized with actual behavior.
- Keep `docs/docker-deployment.md` synchronized with the actual supported Docker/Compose lifecycle, including upgrades, persistence, health checks, backups/restores, rollback limitations, and production boundaries.
- Periodically audit stale wording such as “future” or “planned” for features that have already shipped.
- Review accessibility and color contrast whenever templates/styles change.
- Review live-source/provider classification whenever upstream URL patterns change.
- Keep local development setup reproducible without committing secrets or local databases.
- Prefer fixes for discovered cleanup/debt in the sprint where they are found when the change is safe and focused.
- Select an explicit open-source license before publishing a license badge or claiming licensed reuse; this requires a maintainer/legal choice.

## Deferred ideas

These are intentionally not scheduled yet:

- Additional account/provider integrations using provider-supported OAuth/token mechanisms where available.
- User-owned tuner integrations when a trustworthy local-source contract can be defined.
- Broader guide layouts or grid-style EPG presentation after the current normalized guide behavior is stable.
- More advanced personalization/recommendation features that do not weaken availability or playback truthfulness.

## Backlog hygiene

- Completed work belongs in `docs/sprints.md`, not as stale backlog checkboxes.
- New debt discovered during implementation should be fixed immediately when small and safe; otherwise add it here with enough context to act on later.
- Reprioritization should update both this file and the numbered planned queue in `docs/sprints.md`.
- GitHub issues remain appropriate for externally tracked defects, dependency automation, or work that benefits from separate discussion; this document is the canonical product/sprint planning queue.
