# Prioritized backlog

The detailed acceptance criteria and maintenance backlog live in docs/backlog.md. This root file provides the standards-compatible priority view.

| Priority | Item | Target | Status |
| --- | --- | --- | --- |
| P0 | Keep CI, migrations, full test discovery, Docker startup, health checks, and local test environment clean | Continuous | Active |
| P0 | Repository standards, governance docs, verified README badges, and validation automation | Maintenance | Merged #155 |
| P0 | Select an explicit open-source license | Maintainer/legal decision | Blocked on choice |
| P1 | Live TV accessibility flow audit | Sprint 120 | Merged #157 |
| P1 | Live TV request/database efficiency audit | Sprint 121 | Merged #158 |
| P1 | Operator EPG/source diagnostics | Sprint 122 | Merged #159 |
| P1 | Validate SMB guest-entertainment pilot demand and willingness to pay | Commercial validation | Planned |
| P1 | Operator-configurable guest branding for pilot demos | Sprint 125 | Merged #164 |
| P1 | Operator-configurable guest default region | Sprint 126 | Merged #165 |
| P1 | Guest-first account prompt control for pilot deployments | Sprint 127 | Merged #166 |
| P1 | Staff operator dashboard for pilot configuration/health | Sprint 128 | Merged #167 |
| P1 | Warn when guest region is missing from EPG refresh configuration | Sprint 129 | Active |
| P1 | Next legitimate EPG/source adapter if it meets provenance/trust contracts | Sprint 123 | Evaluated; no-go under current constraints |
| P1 | Production-readiness hardening | Sprint 124 | Merged #161 |
| P2 | Provider-supported account integrations | Future | Backlog |
| P2 | User-owned tuner integration with explicit trustworthy source contract | Future | Backlog |

Reprioritize when CI/security defects, testing findings, or credible customer evidence make another item more valuable. Do not infer completion from this table; completed sprint outcomes belong in docs/sprints.md.
