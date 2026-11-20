# Product vision and sprint plan

**Vision:** Make aitv the fastest trustworthy way to see what is on and reach a legitimate viewing destination, while building toward an SMB-testable guest entertainment guide without becoming a retransmission service.

The detailed historical sprint ledger and current numbered queue are maintained in docs/sprints.md. That file remains the canonical detailed record to avoid duplicating more than one hundred completed sprint entries.

## Current state

- Sprint 119: merged — empty schedule-day navigation.
- Sprint 120: merged — Live TV accessibility flow audit and user-controlled auto-refresh.
- Sprint 121: merged — Live TV request/query efficiency audit.
- Sprint 122: merged — Operator EPG/source diagnostics.
- Sprint 123: PR #160 — source evaluation completed with no eligible second adapter under current licensing/cost constraints.
- Next planned product sprint: Sprint 124 — production-readiness hardening.
- Repository standards adoption is active maintenance work and does not renumber already planned product sprints.
- Commercialization hypotheses and pilot milestones are tracked in docs/commercialization.md.

## Delivery rule

After a sprint merges, refresh main, verify the local Docker environment, update sprint/backlog/release-impact documentation, and proceed to the next ready task. Break/fix and standards/security work may preempt planned feature work when higher priority.

Do not mark a sprint complete merely because code exists; the final head must pass required checks and relevant deployment/user workflows must be verified.
