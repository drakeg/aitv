# AITV agent operating instructions

These instructions apply to human and AI contributors working in this repository. Project-specific requirements take precedence over reusable repository standards when they conflict.

## Mission

Build aitv into a reliable, legitimate TV/movie discovery and Live TV guide product that saves users time finding what is on and where it can legally be watched. Treat the project as commercially testable while preserving its source-trust and playback-safety boundaries.

## Development loop

Use **Build → Deploy → Test → Fix → Redeploy → Continue**.

- Work in small reviewable branches and pull requests from current main.
- Continue to the next ready task after a successful sprint or fix; do not stop merely because CI or a deployment succeeds.
- Treat failed CI, tests, Docker startup, health checks, migrations, warnings, and broken user workflows as high-priority defects.
- Do not claim a test, deployment, migration, or fix succeeded unless it was verified.
- Preserve persistent data; never use destructive volume/database commands without explicit authorization.
- Keep local Docker testing LAN-capable when appropriate through configurable host binding and DJANGO_ALLOWED_HOSTS.

## Product and trust boundaries

- Never fabricate provider deep links, streaming availability, schedules, episode metadata, authentication state, or source provenance.
- Do not add scraped streams, DRM bypasses, credential replay, mystery IPTV/M3U feeds, or untrusted playback URLs.
- Keep schedule metadata separate from playback destinations.
- Keep personalization account-scoped.
- Prefer false negatives over falsely labeling a URL as direct playback.
- Keep public health/readiness output sanitized; operator-only details must not leak upstream errors or secrets.

## Agile and documentation

Maintain and synchronize:

- SPRINTS.md and docs/sprints.md
- BACKLOG.md and docs/backlog.md
- AGENTS.md
- CONTRIBUTING.md
- RELEASES.md
- SECURITY.md
- README.md
- focused architecture, Docker, product, and commercialization docs

Newly discovered cleanup should be fixed in the current PR when safe and focused; otherwise record it in the backlog with enough context to act on later.

## README badges

The bounded badge block directly below the README H1 is generated conservatively by scripts/badges.py.

- Inspect actual manifests, requirements, Docker/Compose files, workflows, releases, and licensing before claiming support.
- Show versions only when verified.
- Use live GitHub Actions and Shields.io statistics where applicable.
- Never hardcode passing CI/security status.
- Do not invent release or license badges when the repository has no published release or license.
- Run python3 scripts/badges.py --mode check when stack/workflow metadata changes.

## Testing and deployment

Before a PR is ready, run the applicable checks:

- python manage.py check
- python manage.py makemigrations --check --dry-run
- full Django tests
- docker compose config --quiet
- repository standards audit/badge validation
- focused workflow tests for changed behavior

The supported project runtime is defined by repository Docker/CI configuration, not by an arbitrary host Python installation.

## Commercialization

Prioritize changes that improve a credible SMB pilot, save customer/staff time, reduce support burden, improve trust, or shorten the path to a paid trial. Keep market validation, pricing, customer feedback, and revenue clearly labeled as hypotheses until verified.

## GitHub workflow

- Respect branch protections and required checks.
- Use pull requests for reviewable changes and keep descriptions accurate.
- Include implementation, test/deployment evidence, risks/non-goals, and relevant documentation updates.
- Keep this repository independent; do not connect authentication, databases, services, or runtime dependencies to unrelated Mad Mallard projects unless explicitly requested.
- Follow drakeg/madmallard-repository-standards as a reusable baseline without overwriting stricter aitv-specific requirements.
