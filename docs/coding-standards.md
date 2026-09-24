# Coding standards

These standards apply to all aitv feature, maintenance, and hotfix sprints.

## Design principles

- Prefer small, explicit changes over broad refactors.
- Treat live-source data as untrusted input. Validate shape, identity, region, and destination semantics before presenting it as watchable.
- Never fabricate provider deep links, availability, episode metadata, or authentication state.
- Keep personalization account-scoped; neutral/default behavior must not inherit another user's choices.
- Keep source adapters separate from presentation logic where practical.
- Favor deterministic behavior and stable ordering so upstream changes do not create arbitrary UI churn.

## Python and Django

- Follow PEP 8 and existing repository conventions.
- Use descriptive names and focused helpers; avoid hidden side effects.
- Keep views thin enough to understand and move reusable source/provider logic into content services or provider modules.
- Validate POST input against explicit allowlists/choices.
- State-changing requests must remain POST-only and CSRF-protected.
- Database schema changes require migrations and focused regression coverage.
- Avoid N+1 database work and repeated upstream requests in request-time loops.

## JavaScript and templates

- Progressive enhancement must preserve a usable server-rendered page.
- UI changes should avoid full-page reloads when the existing interaction is asynchronous.
- Keep accessibility semantics, visible labels, and safe external-link attributes.
- Do not use JavaScript to turn metadata/listing URLs into claimed direct-playback URLs.
- Preserve stable DOM/data attributes when tests or asynchronous controls depend on them.

## External sources and playback

- An upstream URL is not automatically a direct-watch URL.
- Direct-watch recognition must be supported by an explicit provider/source rule or an authoritative source contract.
- Prefer false negatives over falsely labeling an unrelated page as playback.
- Do not add scraping, DRM bypasses, credential replay, pirated IPTV feeds, or mystery M3U playlists.
- Live/EPG sources must record provenance and access semantics (free, ads, subscription, provider sign-in, OTA, rent/buy, or other).
- Provider authentication should use supported OAuth/token/session mechanisms where available; never commit or centrally store raw provider passwords.

## Tests and CI

- Every behavior change needs meaningful regression coverage at the narrowest useful layer plus integration coverage when boundaries interact.
- Test representative middle states and failure/fallback paths, not only happy-path edges.
- Do not weaken a correct regression merely to make CI green; fix the behavior or update an assertion only when the product contract intentionally changed.
- `python manage.py check` and the complete test suite must pass in GitHub Actions before a PR is ready.

## Documentation and sprint hygiene

- Each sprint updates implementation, tests, and relevant docs together.
- Record each sprint in `docs/sprints.md` with goal, principal behavior, PR, and outcome.
- Update README when capabilities, configuration, architecture, local operation, or security boundaries change.
- Keep `docs/agile.md`, this file, and focused product/operations docs consistent with the code.
