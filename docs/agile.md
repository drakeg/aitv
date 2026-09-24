# Agile delivery and quality policy

aitv uses small, reviewable sprint increments. The current main branch is the source of truth for every new sprint branch.

## Sprint workflow

1. Verify the previous pull request is actually merged and identify the exact current main SHA.
2. Create the next sprint branch from that SHA.
3. Keep the change set focused on the sprint goal; avoid unrelated refactors.
4. Update implementation, regression tests, and relevant documentation together.
5. Open a pull request describing behavior, non-goals, migrations/dependencies, and operational impact.
6. Treat GitHub Actions as the readiness gate. A PR is not called green/ready until the current head SHA has completed CI successfully.
7. After merge, verify GitHub recorded the merge and re-read main before beginning the next sprint.\n8. Keep `docs/sprints.md` current so sprint history survives beyond chat context.\n9. Apply `docs/coding-standards.md` to feature, maintenance, and hotfix work.

## Definition of done

A sprint is complete only when all applicable items are true:

- The intended behavior is implemented without unrelated changes.
- New or changed behavior has meaningful regression coverage.
- Existing tests are updated when intentional behavior changes make assertions stale; tests should validate behavior rather than incidental formatting where practical.
- README and focused docs reflect changes to user-visible behavior, configuration, architecture, data-source semantics, security boundaries, or operations.
- Database changes include migrations and migration-focused tests where appropriate.
- Static JavaScript/CSS changes that rely on cache-busting update the corresponding asset version.
- No generated artifacts, secrets, credentials, or local databases are committed.
- Django checks and the complete automated test suite pass in CI.
- The PR description states important non-goals so scope remains auditable.

## Ongoing review

Maintenance sprints should periodically audit the repository rather than waiting for a feature to expose debt. Review areas include:

- duplicated or unnecessarily expensive request/database work;
- stale or contradictory documentation;
- brittle tests that assert implementation trivia instead of behavior;
- live-source/provider truthfulness and safe fallback behavior;
- authentication, CSRF, secret handling, and provider-auth boundaries;
- SQLite/Docker operational reliability;
- stale generated files and dependency hygiene;
- divergence between documented product behavior and the current UI.

Findings should be handled as focused sprint work, with tests and documentation updated in the same pull request.


### Regression-test accuracy

Pagination/navigation regressions must exercise representative middle-state behavior, not only edge pages that can mask current-page bugs.
