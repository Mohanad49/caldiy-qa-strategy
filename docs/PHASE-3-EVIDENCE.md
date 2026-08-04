# Phase 3 Browser, Timezone and Accessibility Evidence

## Controlled boundary

These results apply to Cal.diy `v6.2.0`, commit
`1c193cca8682b33b9866c792186033f7ef886682`, running in this repository's
local Docker environment. They are not evidence about current hosted Cal.com
or current Cal.diy. The original checkpoint was produced on 2026-07-31; the
complete local layer was rerun during the 2026-08-05 public-release audit. CI
and TestPulse evidence is recorded separately in `PHASE-5-CI.md`.

## Measured local results

| Command | Result | Measured duration | Evidence boundary |
|---|---:|---:|---|
| `make test-e2e` | 12/12 passed | 103.99 s | Chromium lifecycle plus Firefox lifecycle smoke |
| `make test-bdd` | 3/3 scenarios, 18/18 steps passed | 33.33 s | Booking, rescheduling and cancellation only |
| `make test-timezones` | 14/14 passed | 89.92 s | Chromium with an independent pinned `zoneinfo` oracle |
| `make test-a11y` | 1/3 passed, 2/3 failed | 28.75 s | Intentional red gate for serious or critical axe findings |
| `pnpm run test:visual` | 2/2 passed | 14.05 s | Darwin Chromium comparison after a guarded baseline update |

Durations come from the final local JUnit reports, except Cucumber's wall time,
which comes from its final command summary. Reports and Allure input are ignored
locally; CI retains the bounded artifacts described in Phase 5. `make validate`
uses a separate dry-run configuration and does not overwrite the real Cucumber
JSON or JUnit evidence.

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
and notification timestamps. A focused New York-host/Kathmandu-booker journey
also proves local-date rollover, retains the initial and replacement UTC
instants, and checks London-organizer and Kathmandu-attendee email timestamps.

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
local reproduction command. Phase 6 did not exercise the current Cal.diy UI,
so none was promoted or filed upstream. Their explicit disposition is recorded
in `docs/defects/README.md`.

## Visual evidence

Committed Chromium baselines are exactly 1440×900 and 390×844 and are stored
separately for Darwin and Linux because browser text rasterization is
platform-dependent. The calendar and timeslot grid sections are masked as
fixed units because their child count and geometry vary with the server's real
date; event metadata, controls, branding and responsive shell remain compared.
An update is refused unless the caller supplies `CONFIRM=caldiy-qa-strategy`.
The guarded Darwin update was inspected and an ordinary local comparison passed.
