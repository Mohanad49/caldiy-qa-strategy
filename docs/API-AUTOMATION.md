# API v2 automation

## Delivered boundary

Phase 2 exercises the locally built Cal.diy API v2 from the controlled `v6.2.0` commit. It does not call hosted Cal.com, API v1, or a current Cal.diy deployment. The API image remains private and local because the upstream package is marked `UNLICENSED`; runtime provenance and qualification are recorded in `API-V2-RUNTIME.md`.

The suite uses Python 3.12, a locked `uv` environment, pytest with four workers, httpx, strict typing, Ruff, coverage, JSON Schema, OpenAPI validation, pinned `tzdata`, and Allure-compatible result emission.

## Commands

```text
make api-build
make sut-api-bootstrap
make sut-api-smoke
make test-bootstrap
make contracts-verify
make test-api
```

`sut-api-bootstrap` includes the ten-minute runtime qualification. `sut-api-smoke` is the fast health and identity check. `test-api` requires the complete qualified stack and writes ignored local evidence under `test-results/api` and `allure-results/api`.

## Client and data design

The typed client owns authentication, resource-specific API version headers, expected statuses, and response validation:

| Resource | `cal-api-version` |
|---|---|
| Event types | `2024-06-14` |
| Schedules | `2024-06-11` |
| Bookings | `2024-08-13` |
| Slots | `2024-09-04` |

Builders generate names containing the run and xdist worker identities. Factories create schedules, event types, and bookings through supported API endpoints and register cleanup immediately after each validated creation. Cleanup runs in LIFO order and reports a teardown failure without replacing an earlier test failure.

Cal.diy exposes cancellation, not deletion, for bookings. Cleanup therefore terminalizes created bookings before deleting their event types and schedules. Historical cancelled booking rows remain until the guarded project reset removes the local database. This is a SUT API limitation, not a claim that cancellation deletes history.

The `caldiy-fixtures create --json` and `caldiy-fixtures destroy --json` commands expose the same schedule/event-type factory boundary for later TypeScript tests. A local round trip was verified with an emitted manifest, a successful destroy result, and 404 reads for both removed resources.

## Contract policy

`contracts/api-v2/openapi-v6.2.0.json` is copied unchanged from the tagged source and has SHA-256 `e9e662d1183733ee57da8ac02a60891c67e021df47c30b4d6fd29bdad60a0cfb`. `make contracts-verify` compares all 18 operations used by the suite against the canonical runtime `/docs-json`; the accepted runtime matched every operation exactly.

Every documented response is first validated against that unmodified snapshot. Undocumented error statuses are validated against the committed common error-envelope schema and reported as contract omissions. Proven defects in the pinned document use narrow, code-defined projections only after the original validation fails. A projected response is accepted only when the entire response then validates; an unknown mismatch still fails the test.

The tagged snapshot has 14 evidence-backed local compatibility findings in
`docs/findings`. Phase 6 compared every one with current public Cal.diy `main`:
F-002 was reproduced from current source and contract and filed as
[calcom/cal.diy#29904](https://github.com/calcom/cal.diy/issues/29904); F-001,
F-003 and F-004 no longer contain the faulty contract condition; F-005 through
F-014 remain local because their current runtime responses were not reproduced.
The complete disposition is in `docs/defects/README.md`.

## Implemented coverage

The 13 independent pytest cases cover:

- seeded API-key identity, invalid bearer handling, and cross-owner event-type and schedule access;
- event-type create, get, list, update, delete, malformed input, missing fields, and not found;
- schedule create, get, list, default selection, update, invalid timezone, and cleanup;
- slot discovery plus invalid timezone;
- booking create, get, list, reschedule, cancel, past time, outside availability, missing fields, invalid attendee timezone, and not found;
- two requests for the same capacity-one slot, requiring the second request to be rejected.

The contention case is a functional two-request check, not the synchronized 20-request k6 gate planned for Phase 4.

## Local evidence

On 2026-07-31, `make test-api` passed 13 of 13 tests using four xdist workers in 17.58 seconds and reported 77% branch-aware package coverage. The run generated JUnit XML, coverage XML, per-worker contract-deviation/omission reports, and Allure-compatible raw results. These are local results, not a CI claim, and they have not been ingested into TestPulse.

## Remaining limitations

- The local numbers above are Phase 2 evidence; later CI results are documented
  separately in `docs/PHASE-5-CI.md`.
- Mailpit notification correlation belongs to the later browser lifecycle layer,
  not this API suite.
- The suite does not test payments, OAuth providers, API v1, license enforcement, enterprise features, or hosted Cal.com.
- Current-main contract and defect auditing remains informational and does not
  change the controlled `v6.2.0` SUT.
- No performance, accessibility, visual, browser, BDD, or timezone-transition result is implied by this phase.
