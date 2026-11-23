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

### Commercial validation — current state

Sprint 134 completed the non-outreach preparation:

- `docs/pilot-demo.md` provides the repeatable hospitality demo and paid-pilot discovery flow.
- `docs/pilot-interview-template.md` provides one structured evidence record per conversation.
- The product's operator dashboard now exposes operational pilot readiness for a configured location.
- No external operator interview, outreach message, paid-pilot ask, customer commitment, revenue, or willingness-to-pay result has been performed or claimed.

The next commercial-validation action is conducting qualified operator conversations using those materials. External outreach remains pending explicit authorization; that dependency does not block continuous reliability, security, accessibility, documentation, dependency, or defect work.

### Sprint 148 — Guest-first branded home welcome panel

Make the anonymous hospitality experience immediately understandable after a guest follows a printed QR code or digital handoff link.

Acceptance direction:
- Give anonymous guests a prominent branded welcome panel at the top of Home.
- Reuse the existing configured site name and optional welcome text; do not introduce duplicate branding state.
- Make Live TV the primary guest action and provide a secondary in-page jump to movie/show discovery.
- Keep the generic trust-focused fallback copy when no custom welcome message is configured.
- Preserve guest-preview mode in the Live TV CTA so staff can inspect the exact anonymous experience without ending their session.
- Keep signed-in account users on the existing personalized home layout rather than showing the guest hero.
- Preserve HTML escaping for operator-configured welcome text.
- Add regression coverage for default branding, configured branding, signed-in behavior, discovery anchor, and guest-preview navigation.

## Next product priorities

With the planned Sprint 119–124 sequence complete, product work is now evidence-driven:

- validate the SMB hospitality pilot hypothesis in `docs/commercialization.md`;
- prioritize demo/pilot blockers found through real operator conversations;
- keep production reliability, accessibility, source licensing, and test coverage as continuous quality gates;
- do not add infrastructure scale or paid services until measured demand justifies them.

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

- Re-evaluate TV Schedule API as a second EPG source if its Live-plan recurring cost is explicitly authorized; re-check current terms/pricing first.
- Re-evaluate Schedules Direct only with written commercial permission/approval, not an ordinary subscriber account.
- Re-evaluate TheTVDB only with a suitable commercial API arrangement and evidence its schedule data adds material value beyond TVmaze.
- Additional account/provider integrations using provider-supported OAuth/token mechanisms where available.
- User-owned tuner integrations when a trustworthy local-source contract can be defined.
- Broader guide layouts or grid-style EPG presentation after the current normalized guide behavior is stable.
- More advanced personalization/recommendation features that do not weaken availability or playback truthfulness.

## Backlog hygiene

- Completed work belongs in `docs/sprints.md`, not as stale backlog checkboxes.
- New debt discovered during implementation should be fixed immediately when small and safe; otherwise add it here with enough context to act on later.
- Reprioritization should update both this file and the numbered planned queue in `docs/sprints.md`.
- GitHub issues remain appropriate for externally tracked defects, dependency automation, or work that benefits from separate discussion; this document is the canonical product/sprint planning queue.
