# Accessibility

aitv treats accessibility as part of normal feature quality rather than a separate polish phase.

## Live TV flow audit

Sprint 120 audits the Live TV guide and channel schedule as one keyboard and assistive-technology flow.

### Implemented improvements

- A keyboard-visible **Skip to main content** link targets a real main landmark.
- The global navigation has an explicit accessible name.
- The Live TV filter form is exposed as a named search region.
- Guide and schedule result collections use named section landmarks rather than labels on generic containers.
- Channel and schedule rows are explicitly labelled by their visible channel/program headings.
- Guide start/end values use semantic time elements with machine-readable timestamps.
- Trusted Watch actions that open a new tab announce that behavior to assistive technology.
- Live TV pages expose a visible **Pause auto-refresh / Resume auto-refresh** control.
- The pause preference persists in browser local storage and synchronizes across tabs when storage is available.
- If browser storage is unavailable, the pause control still works for the current page through an in-memory fallback.
- Auto-refresh continues to pause when the page is hidden or an interactive element has focus.

## Auto-refresh rationale

The guide refreshes every minute so Now/Next/Later state and countdowns stay current. Keyboard-focus detection alone is insufficient for screen-reader browse mode because browse navigation may not move DOM focus. A persistent user pause control therefore provides an explicit way to stop time-based page reloads without disabling freshness for every user.

## Regression coverage

Django template tests protect the landmarks, named controls and regions, row labelling, semantic times, and new-tab announcements. A lightweight static contract test protects the shared auto-refresh pause behavior without introducing a JavaScript test-framework dependency.

Accessibility should be re-audited whenever Live TV navigation, filters, timed refresh behavior, or shared page landmarks change.
