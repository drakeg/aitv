# Contributing to aitv

Contributions from humans and coding agents are welcome. Keep changes focused, reviewable, tested, and truthful about data sources and playback availability.

## Workflow

1. Start from current main and associate the work with the current sprint, prioritized backlog, or an urgent break/fix.
2. Create a focused branch and use small commits. Conventional Commit prefixes are encouraged.
3. Implement behavior, regression tests, and relevant documentation together.
4. Run the applicable checks:
   - python manage.py check
   - python manage.py makemigrations --check --dry-run
   - python manage.py test
   - docker compose config --quiet
   - python3 scripts/audit.py --check
   - python3 scripts/badges.py --mode check
5. Open a pull request describing user/business value, scope, tests, deployment impact, migrations, security/trust implications, rollback considerations, and non-goals.
6. Resolve CI failures and review feedback before merge.

Routine internal sprint work does not require a separate GitHub issue when the sprint/backlog record already provides traceability. Urgent break/fix work may be expedited but must still be documented.

## Definition of ready

Work is ready when its user/business rationale, boundaries, acceptance criteria, dependencies, and trust/security implications are clear enough to implement without guessing.

## Definition of done

- Acceptance criteria are met.
- Regression coverage is meaningful.
- Django checks, migration-drift checks, full tests, Compose validation, and repository standards checks pass.
- User-visible, architectural, deployment, security, sprint/backlog, commercialization, and release-impact docs are updated when applicable.
- No secrets, local databases, generated junk, or fabricated source/provider claims are committed.
- The pull request is reviewable and the current head has green required checks.

See AGENTS.md, SECURITY.md, RELEASES.md, and docs/agile.md for additional project-specific rules.
