# Security policy

Do not publish credentials, tokens, private user data, sensitive provider information, or working exploits in public issues or pull requests.

For a security vulnerability, use GitHub private vulnerability reporting if enabled. If it is unavailable, contact the repository owner privately before sharing exploit details.

## Project security boundaries

- aitv does not bypass DRM, provider authentication, or access controls.
- Never store or replay raw streaming-provider passwords.
- Do not add scraped streams, unknown IPTV/M3U sources, or guessed provider deep links.
- Upstream/source errors exposed publicly must be sanitized.
- State-changing web actions remain POST-only and CSRF protected.
- Secrets belong in environment/secret storage, never committed .env files or workflow output.
- GitHub Actions should use least privilege; read-only permissions are the default unless a narrowly scoped write is required.

## Supported versions

Until a first public release is intentionally published, security fixes target the current main development line. Supported release lines will be stated here after releases exist.

Dependency and GitHub Action upgrades should be reviewed for security and compatibility; Renovate suggestions are inputs to review, not automatic proof of safety.
