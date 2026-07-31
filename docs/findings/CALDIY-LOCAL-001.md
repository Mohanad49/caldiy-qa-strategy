# CALDIY-LOCAL-001 — Cairo fold omits the second repeated-hour instant

## Status and boundary

- **Status:** Local compatibility finding; not filed upstream
- **Observed against:** Cal.diy v6.2.0, commit `1c193cca8682b33b9866c792186033f7ef886682`
- **Interface:** API v2 `GET /v2/slots`, version `2024-09-04`
- **Oracle:** Python `zoneinfo` forced to the committed `tzdata==2026.3` package
- **Risk area:** Timezone/DST availability correctness

This finding applies only to the controlled historical snapshot. It is not a claim about hosted Cal.com or current Cal.diy. Phase 6 must reproduce it against current Cal.diy and search for duplicates before any upstream report.

## Reproduction

1. Start the complete local stack with `make sut-api-bootstrap`.
2. Run `make test-timezones`.
3. Inspect the `known-cairo-fold-limitation.json` attachment for the `Africa/Cairo` case in the Playwright/Allure results.

The test creates an isolated 60-minute event with daily `00:00`–`23:59` availability in `Africa/Cairo`, then requests slots across 28–31 October 2026.

## Expected

At the 29 October 2026 fold, Cairo repeats the local `23:00` hour:

- `2026-10-29T23:00:00+03:00` maps to `2026-10-29T20:00:00Z`.
- `2026-10-29T23:00:00+02:00` maps to `2026-10-29T21:00:00Z`.

Both instants are distinguishable and could represent separate capacity in the repeated wall-clock hour. New York and London expose both fold instants under the same test design.

## Actual

Cal.diy returns `2026-10-29T23:00:00.000+03:00`, then advances to `2026-10-30T00:00:00.000+02:00`. It does not return the repeated `2026-10-29T23:00:00+02:00` instant.

The test retains the exact UTC instants, offsets, transition data, and `tzdata` version with the report. Browser conversion agrees with the independent oracle for every instant that Cal.diy does return.

## Impact hypothesis

A host intending to offer capacity throughout the repeated Cairo hour may expose only one of the two possible instants. That can reduce bookable capacity or make host and booker expectations disagree around the fold. This impact is a hypothesis; no production frequency or hosted-service impact has been measured.

## Related observed limitations

These are recorded behavior, not classified defects:

- Cal.diy omits 90-minute Sydney slots that would cross the 2026 spring-forward instant; the suite retains the returned boundary slots.
- A historical Cairo 2023 slot request returns HTTP 200 with an empty slot set. Future-transition coverage remains active and no database bypass is used.
