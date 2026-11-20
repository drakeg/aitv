# EPG source evaluation

Last reviewed: 2026-11-19.

This document records candidate schedule-source decisions for the normalized Live TV/EPG architecture. It is an engineering and product gate, not permission to purchase a service or accept new licensing terms.

## Required source contract

A new EPG adapter must provide enough authoritative data to satisfy all of these requirements:

- stable source identities for channels and airings/programs;
- timezone-aware or unambiguous start/end timestamps;
- explicit region/country semantics;
- documented refresh/snapshot completeness behavior;
- terms that permit aitv's intended use;
- no requirement to infer or scrape playback destinations;
- schedule metadata remains separate from playback destinations;
- failures can be distinguished from legitimate empty schedules;
- credentials and costs are explicitly configured rather than hidden in source code.

If a source cannot satisfy these requirements, it must not be integrated merely to increase channel count.

## Current source: TVmaze

**Decision: keep as the current authoritative normalized schedule source.**

Official API documentation: https://www.tvmaze.com/api

Relevant facts:

- Public REST API is available without a paid application plan.
- TVmaze documents the API data under CC BY-SA and permits use for any purpose subject to attribution and ShareAlike requirements.
- The existing adapter already preserves stable source identities and authoritative timezone-aware schedule timestamps.
- The existing refresh implementation has complete-snapshot validation, reconciliation, malformed-row fail-closed behavior, and explicit provenance.

Engineering follow-up: retain visible/source-linked TVmaze attribution anywhere required by the API license and review ShareAlike obligations before a commercial public launch.

## Candidate: TV Schedule API

**Decision: technically suitable, commercially blocked until a paid plan is explicitly authorized.**

Official sources:

- Documentation: https://tvschedule.org/documentation
- Listings: https://tvschedule.org/documentation/listings
- Pricing: https://tvschedule.org/pricing
- Terms: https://tvschedule.org/terms

Technical fit:

- Channel and listing IDs are documented as stable.
- Schedule start/stop values are UTC timestamps.
- Country endpoints use two-letter country codes.
- A channel schedule returns explicit airing rows with stable listing IDs, channel IDs, start/stop times, titles, categories and optional episode identity.
- The API is explicit about plan-limited windows, which could be modeled as a source capability rather than guessed.

Commercial blocker:

- The free plan is limited to yesterday's listings and directory access.
- Current/future schedules suitable for aitv's Live TV guide require the paid Live plan, currently advertised at $39/month.
- The terms permit using data in an application's own screens but prohibit redistribution/resale of the raw data and rebuilding a competing listings database.

Unblock condition:

1. Explicit authorization for the recurring API cost.
2. Re-review the then-current pricing/terms.
3. Store the key only through environment/secret configuration.
4. Implement the adapter behind the existing normalized schedule-source contract with contract tests and plan-window failure handling.

Do not use the free yesterday-only plan as a fake live source.

## Candidate: Schedules Direct

**Decision: not eligible for the planned commercial product under the standard subscriber agreement.**

Official sources:

- Subscriber agreement: https://schedulesdirect.org/sagreement
- FAQ: https://www.schedulesdirect.org/faq
- Supported regions: https://schedulesdirect.org/regions
- Approved software: https://schedulesdirect.org/approvedsoftware

Technical fit:

- JSON schedule data is available for multiple countries and provides a useful future horizon.

Licensing blocker:

- The subscriber agreement limits licensed data to personal, non-commercial use.
- Access is tied to approved software.
- The agreement explicitly excludes commercial EPG/software applications unless prior written consent is obtained.
- The approved-software guidance says unapproved software may not use the service.

Unblock condition:

- Written commercial permission/license from Schedules Direct and confirmation that aitv is approved for the intended use.

A normal membership or free trial is not sufficient authorization for aitv's SMB/commercial direction.

## Candidate: TheTVDB

**Decision: defer pending a commercial licensing model and evidence that its schedule data materially improves the Live TV guide.**

Official sources:

- API/data licensing: https://thetvdb.com/api-information
- API licensing FAQ: https://support.thetvdb.com/kb/faq.php?id=62

Relevant facts:

- TheTVDB supports commercial API use, but API keys require either a commercial license or a user-supported subscription model.
- Commercial licensing fees depend on usage/company/data use rather than presenting a no-cost commercial tier.
- TheTVDB is primarily a metadata provider; an integration would need to demonstrate that its schedule/airing coverage adds value beyond the current source without weakening the authoritative-snapshot contract.

Unblock condition:

1. A defined commercial API arrangement acceptable for aitv.
2. Confirmation of schedule/airing endpoints and completeness semantics needed by the EPG contract.
3. A measurable product benefit over TVmaze.

## Disallowed shortcuts

The following do not qualify as new EPG sources:

- scraping TV-guide websites;
- consuming mystery XMLTV/M3U feeds with unclear rights;
- treating provider metadata or search results as an authoritative schedule;
- using a personal/non-commercial subscription for a commercial pilot;
- adding a paid API and expecting the maintainer to discover the recurring charge later;
- republishing a source's raw schedule feed when its terms prohibit redistribution.

## Sprint 123 outcome

No second source currently satisfies the combination of:

1. technically adequate live/current schedule data;
2. clear compatibility with aitv's commercial direction;
3. no unapproved recurring cost; and
4. the existing provenance/trust contract.

Sprint 123 therefore completes with **no adapter added**. This is an intentional product/trust decision, not an unfinished implementation.

The strongest technical candidate is TV Schedule API, but implementing its live window is blocked on explicit authorization for a paid plan. Re-evaluate candidates when pricing, licensing, product demand, or customer-funded pilot requirements change.
