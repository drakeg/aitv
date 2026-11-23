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
| P1 | Validate SMB guest-entertainment pilot demand and willingness to pay | Commercial validation | Demo package ready; external interviews/outreach not yet authorized |
| P1 | Operator-configurable guest branding for pilot demos | Sprint 125 | Merged #164 |
| P1 | Operator-configurable guest default region | Sprint 126 | Merged #165 |
| P1 | Guest-first account prompt control for pilot deployments | Sprint 127 | Merged #166 |
| P1 | Staff operator dashboard for pilot configuration/health | Sprint 128 | Merged #167 |
| P1 | Warn when guest region is missing from EPG refresh configuration | Sprint 129 | Merged #168 |
| P1 | Copyable guest launch URLs for pilot distribution | Sprint 130 | Merged #169 |
| P1 | Permission-aware operator dashboard actions | Sprint 131 | Merged #170 |
| P1 | Inline guest settings on operator dashboard | Sprint 132 | Merged #171 |
| P1 | Operator pilot-readiness checklist | Sprint 133 | Merged #172 |
| P1 | Hospitality pilot demo/evidence package | Sprint 134 | Merged #173 |
| P1 | One-click guest launch URL copy controls | Sprint 135 | Merged #175 |
| P1 | Preserve/display source episode metadata in Live TV | Sprint 136 | Merged #177 |
| P1 | Current-program progress indicators in Live TV | Sprint 137 | Merged #178 |
| P1 | True anonymous guest preview for staff operators | Sprint 138 | Merged #179 |
| P0 | Debug/staticfiles reliability for local/test rendering | Sprint 139 | Merged #180 |
| P0 | Remove debug/test WhiteNoise STATIC_ROOT warning | Sprint 140 | Merged #181 |\n| P0 | Tested SQLite backup/verification and guarded restore tooling | Sprint 141 | Active |
| P1 | Next legitimate EPG/source adapter if it meets provenance/trust contracts | Sprint 123 | Evaluated; no-go under current constraints |
| P1 | Production-readiness hardening | Sprint 124 | Merged #161 |
| P2 | Provider-supported account integrations | Future | Backlog |
| P2 | User-owned tuner integration with explicit trustworthy source contract | Future | Backlog |

Reprioritize when CI/security defects, testing findings, or credible customer evidence make another item more valuable. Do not infer completion from this table; completed sprint outcomes belong in docs/sprints.md.
