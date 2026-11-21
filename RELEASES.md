# Releases and versioning

aitv uses Semantic Versioning for published releases.

- **MAJOR**: incompatible user-facing, integration, deployment, data-contract, or supported-API changes.
- **MINOR**: backward-compatible product capabilities such as new discovery/guide features, source adapters, operator capabilities, or major workflow improvements.
- **PATCH**: backward-compatible defect, security, compatibility, documentation, or operational fixes where a release is useful to consumers.

A merge does not automatically require a release.

## Current release posture

Until the first intentional public release is published, main is the supported development line. Do not display a release badge or claim a current release until a GitHub release/tag actually exists.

A first stable v1.0.0 should require:
- a clearly defined supported deployment model;
- green CI and repository standards checks;
- tested migration/backup/restore procedures;
- documented security and source-trust boundaries;
- a coherent user workflow suitable for demonstration/pilot;
- maintainer approval of the public compatibility contract.

Pre-stable releases may use v0.x.y when a tested milestone is useful for pilot users.

After Sprint 124, the repository has a supported single-host/pilot production runtime. That is necessary but not sufficient for a public open-source release. An explicit repository license is still required before claiming licensed open-source redistribution, and a pilot release should be cut only when the intended demo/pilot workflow is verified on the release commit.

## Release checklist

- Required pull requests reviewed and merged.
- CI, migration-drift, Docker/health, and standards checks green.
- No exposed secrets or fabricated provider/source claims.
- README.md, SPRINTS.md, BACKLOG.md, focused docs, and commercialization notes current.
- Migration, deployment, rollback, and backup implications documented.
- Badge claims revalidated.
- Release notes describe user-visible changes and compatibility/migration requirements.
- Version/tag choice manually verified before publishing.

Security fixes and regressions may justify an expedited patch release. Breaking behavior must include migration guidance and target an appropriate major version.
