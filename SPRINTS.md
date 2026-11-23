# Product vision and sprint plan

**Vision:** Make aitv the fastest trustworthy way to see what is on and reach a legitimate viewing destination, while building toward an SMB-testable guest entertainment guide without becoming a retransmission service.

The detailed historical sprint ledger and current numbered queue are maintained in docs/sprints.md. That file remains the canonical detailed record to avoid duplicating more than one hundred completed sprint entries.

## Current state

- Sprint 119: merged — empty schedule-day navigation.
- Sprint 120: merged — Live TV accessibility flow audit and user-controlled auto-refresh.
- Sprint 121: merged — Live TV request/query efficiency audit.
- Sprint 122: merged — Operator EPG/source diagnostics.
- Sprint 123: merged — source evaluation completed with no eligible second adapter under current licensing/cost constraints.
- Sprint 124: merged — hardened single-host/pilot production deployment.
- Sprint 125: merged — operator-configurable guest branding for pilot/demo usability.
- Sprint 126: merged — operator-configurable default guest region, with account-level region override preserved.
- Sprint 127: merged — operator-controlled guest-first navigation that can hide Login/Register prompts.
- Sprint 128: merged — staff operator dashboard for guest configuration, safe EPG health, and preview links.
- Sprint 129: merged — operator warning for guest-region/EPG refresh configuration mismatch.
- Sprint 130: merged — staff-only copyable guest home and Live TV launch URLs for pilot distribution.
- Sprint 131: merged — permission-aware operator configuration and diagnostics actions.
- Sprint 132: merged — permission-gated inline guest settings on the operator dashboard.
- Sprint 133: merged — operator pilot-readiness checklist for guest settings, EPG coverage, and guide health.
- Sprint 134: merged — hospitality pilot demo guide and structured interview/evidence package.
- Sprint 135: merged — accessible one-click Copy controls for guest Home and Live TV launch URLs.
- Sprint 136: merged — preserve and display authoritative per-airing episode title/season/number metadata.
- Sprint 137: merged — accessible current-program progress indicators from normalized airing timing.
- Sprint 138: merged — true anonymous guest preview for staff operators without ending the operator session.
- Sprint 139: merged — restore reliable development/test static rendering while retaining production manifest storage.
- Sprint 140: merged — remove debug/test WhiteNoise STATIC_ROOT warnings while preserving production middleware/static behavior.
- Sprint 141: merged — add tested SQLite backup, verification, and guarded restore tooling for single-host pilot operations.
- Sprint 142: merged — add an opt-in scheduled verified-backup profile with bounded retention for single-host pilot deployments.
- Sprint 143: merged — make scheduled-backup integrity/freshness visible through Docker health.
- Sprint 144: active — exercise the actual production backup profile end-to-end in CI.
- Commercial validation is now prepared for operator interviews; external outreach and paid-pilot asks remain unperformed and require explicit authorization.
- After Sprint 124, prioritize commercial pilot validation and defects/opportunities discovered from real testing rather than inventing another feature sprint.
- Repository standards adoption is active maintenance work and does not renumber already planned product sprints.
- Commercialization hypotheses and pilot milestones are tracked in docs/commercialization.md.

## Delivery rule

After a sprint merges, refresh main, verify the local Docker environment, update sprint/backlog/release-impact documentation, and proceed to the next ready task. Break/fix and standards/security work may preempt planned feature work when higher priority.

Do not mark a sprint complete merely because code exists; the final head must pass required checks and relevant deployment/user workflows must be verified.
