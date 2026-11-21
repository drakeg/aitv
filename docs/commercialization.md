# Commercialization hypothesis

This document records product-market-fit hypotheses for aitv. It does **not** claim validated demand, customers, revenue, or willingness to pay.

## Candidate SMB customer

Primary validation target: independent hospitality operators such as RV resorts, boutique hotels, campgrounds, and professionally managed vacation-rental portfolios that want a simple guest-facing entertainment guide without operating or rebroadcasting television streams.

## Problem hypothesis

Guests often face fragmented TV schedules, streaming apps, regional provider availability, and unclear channel/source information. Staff may repeatedly answer “what is on?” and “where can I watch it?” questions without having a trustworthy unified view.

## Value proposition hypothesis

aitv could provide a branded, region-aware guest entertainment guide that:

- shows current/next programming from legitimate schedule sources;
- points only to trusted provider/source-supplied destinations;
- avoids rebroadcasting content or bypassing provider authentication;
- reduces staff support questions;
- gives operators a lightweight amenity they can link from Wi-Fi portals, QR codes, welcome messages, or guest tablets. **Sprint 130 exposes same-site guest home and Live TV launch URLs on the operator dashboard for these distribution channels.**

## Pilot MVP

The fastest credible paid-pilot scope is intentionally small:

1. One hospitality location.
2. Branded landing page and region configuration. **Brand name/welcome-message configuration shipped in Sprint 125; operator-level guest default region configuration is implemented in Sprint 126, while signed-in viewers retain account-specific overrides.**
3. Live TV guide plus trusted watch/provider destinations.
4. Mobile-friendly guest experience requiring no guest account for basic viewing. **Sprint 127 adds an operator option to hide Login/Register prompts for a guest-first deployment while leaving account functionality available when desired.**
5. Operator health/status view and simple configuration. **Sprint 133 adds a required-readiness checklist for saved guest settings, EPG-region coverage, and healthy guide data without implying customer validation.** **Sprint 132 lets authorized operators edit the core guest-facing settings directly from the operator dashboard while preserving native Django permissions.** **Sprint 131 makes dashboard configuration/diagnostic actions permission-aware so read-only staff are not sent to inaccessible Admin pages.** **Sprint 128 adds a staff-only dashboard summarizing guest configuration and sanitized EPG health with direct preview/settings links.** **Sprint 129 adds a configuration-readiness warning when the location's guest region is not included in the recurring EPG worker regions.**
6. No custom streaming infrastructure, DRM handling, or provider credential storage.

## Pricing hypothesis

Unvalidated starting hypothesis:

- **Pilot:** $49/month per location after a short evaluation period.
- **Standard:** $79/month per location when branding/operator controls are mature.
- Optional setup/custom branding could be tested separately only after demand is demonstrated.

These are testing hypotheses, not market-validated prices.

## Alternatives and competition

Consumer products such as TV Guide, JustWatch, and streaming-platform guides already solve parts of discovery. The proposed differentiation is a lightweight operator-branded guest experience, source-truthfulness, location configuration, and reduced staff support rather than trying to out-catalog consumer discovery platforms.

## Validation milestones

Do not build large commercial-only features before evidence exists.

1. Prepare a demo usable by a hospitality operator. **Sprint 134 prepares the demo guide and structured evidence template; no external validation is claimed by that preparation alone.**
2. Interview at least 10 qualified operators about the problem and current workaround.
3. Ask for a paid pilot rather than relying on positive feedback alone.
4. Record objections and required features without inventing demand.
5. Prioritize only features that materially improve demo-to-pilot conversion, staff time savings, guest usability, or operational trust.
6. First meaningful commercial milestone: one paying pilot location.

## Product metrics to test

- Operator demo-to-pilot conversion.
- Guest guide sessions per occupied room/site, when privacy-safe measurement exists.
- Staff-reported reduction in entertainment-related questions.
- Percentage of displayed current airings with a legitimate actionable destination.
- Operator retention after the pilot period.

No metric should be reported as achieved until real usage data exists.
