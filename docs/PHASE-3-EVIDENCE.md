# Phase 3 Browser, Timezone and Accessibility Evidence

## Controlled boundary

These results apply to Cal.diy `v6.2.0`, commit
`1c193cca8682b33b9866c792186033f7ef886682`, running in this repository's
local Docker environment. They are not evidence about current hosted Cal.com
or current Cal.diy. They were produced locally on 2026-07-31 and have not been
ingested into TestPulse or reproduced in CI.

## Measured local results

| Command | Result | Measured duration | Evidence boundary |
|---|---:|---:|---|
| `make test-e2e` | 12/12 passed | 75.52 s | Chromium lifecycle plus Firefox lifecycle smoke |
| `make test-bdd` | 3/3 scenarios, 18/18 steps passed | 25.93 s | Booking, rescheduling and cancellation only |
| `make test-timezones` | 13/13 passed | 61.84 s | Chromium with an independent pinned `zoneinfo` oracle |
| `make test-a11y` | 1/3 passed, 2/3 failed | 26.60 s | Intentional red gate for serious or critical axe findings |
| `pnpm run test:visual` | 2/2 passed | 12.88 s | Chromium snapshot comparison after a guarded baseline update |

Durations come from the locally generated JUnit reports. The ignored reports
and Allure input are retained only as local evidence until Phase 5 defines CI
artifact retention and TestPulse ingestion.

## Browser lifecycle design

Chromium is authoritative for the complete lifecycle. Firefox repeats the
tagged lifecycle smoke path. Test fixtures create event types and schedules
through the Phase 2 Python CLI, use isolated guest contexts, correlate Mailpit
messages, and destroy resources through supported interfaces.

The covered workflows are registration when enabled, seeded-user login, event
type creation, availability editing, guest booking, rescheduling and
cancellation. Registration cleanup uses Cal.diy's supported account-deletion
mutation. Booking cleanup cancels rather than deletes because API v2 does not
expose booking deletion.

The local fixture has no external calendar credentials. Initial booking does
not emit Cal.diy's normal guest confirmation; it emits the organizer's
`[Action Required] Confirmed` message. The suite correlates that message for the
initial booking and correlates guest-facing lifecycle messages for reschedule
and cancellation. This is an environment limitation, not a claim about hosted
Cal.com notification behavior.

## Selective BDD boundary

The single Cucumber feature contains exactly three journeys: booking,
rescheduling and cancellation. It reuses the Playwright world, page objects,
fixture CLI and cleanup hooks. API boundary checks, OpenAPI validation,
timezone matrices, accessibility and visual assertions remain outside Gherkin.

## Timezone and DST evidence

The matrix exercises UTC, New York, London, Cairo, Kolkata, Kathmandu, Eucla,
Sydney and Phoenix. It covers fractional offsets, DST gaps and folds, opposing
hemispheres, non-DST/DST pairings, rescheduling, boundary-spanning durations
and notification timestamps.

Python `zoneinfo` is forced to the exactly pinned `tzdata==2026.3` package and
generates the expected transitions and UTC instants. Browser contexts control
`timezoneId`. Playwright Clock is used only for browser-side “now” behavior;
the test separately confirms that the server clock was not frozen. Exact UTC
instants and the oracle tzdata version are attached to the local results.

The run produced one evidence-backed snapshot finding:

- [`CALDIY-LOCAL-001`](findings/CALDIY-LOCAL-001.md) — Cairo's 2026 fall-back
  slot response omits one repeated-hour UTC instant.

Two observations remain limitations rather than classified defects: Cal.diy
returned an empty HTTP 200 slot window for the historical Cairo 2023 case, and
it omitted a 90-minute Sydney slot that crosses the spring-forward gap. Future
transition coverage remains active; no SQL workaround was introduced.

## Accessibility evidence

The axe gate scans the public booking page, guest-details step and cancellation
panel for serious or critical violations. It uses a deterministic light color
scheme, reduced motion, settled network state and loaded fonts. No axe rules or
DOM regions are suppressed.

The cancellation panel passed. The other two surfaces kept the gate red and
produced three local findings:

- [`CALDIY-LOCAL-002`](findings/CALDIY-LOCAL-002.md) — critical unnamed calendar overlay switch.
- [`CALDIY-LOCAL-003`](findings/CALDIY-LOCAL-003.md) — serious guest-details text contrast failures.
- [`CALDIY-LOCAL-004`](findings/CALDIY-LOCAL-004.md) — serious Terms and Privacy link distinction failure.

The findings contain the affected surface, rule, impact, observed nodes and
local reproduction command. None has been filed upstream. Phase 6 requires
duplicate searching and reproduction against current Cal.diy before any
upstream report is eligible.

## Visual evidence

Committed Chromium baselines are exactly 1440×900 and 390×844. Only the month
label, calendar days, time choices and selected-date heading are masked because
they vary with fixture dates. An update is refused unless the caller supplies
`CONFIRM=caldiy-qa-strategy`; the ordinary visual command compared cleanly
against the resulting baselines.
