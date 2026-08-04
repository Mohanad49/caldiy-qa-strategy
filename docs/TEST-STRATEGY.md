# Cal.diy Test Strategy

## Document purpose

This strategy defines the quality risks, test boundaries, evidence, and release
criteria for an independent QA engagement against Cal.diy. It is written for a
product stakeholder deciding what confidence the engagement can provide and for
an engineer who must implement the tests without quietly changing that scope.

This document records the delivered engagement and its enduring boundaries.
The repository README is the source of truth for current status and measured
results; subsystem documents retain the evidence behind each phase.

## Product and version boundary

The system under test is the public `calcom/cal.diy` repository at tag `v6.2.0`,
commit `1c193cca8682b33b9866c792186033f7ef886682`. It is run from the immutable
upstream container identified in `infra/compose.yml`.

The tag predates the April 2026 split in which Cal.com moved its production
codebase to a private repository and renamed the public repository Cal.diy.
Results from this engagement describe this snapshot only. They must not be
presented as coverage of the current hosted Cal.com service.

The product capabilities relevant to this engagement are:

- host identity, event types, schedules, and availability;
- public slot discovery and guest booking;
- booking rescheduling and cancellation;
- booking lifecycle notifications captured by a local SMTP sink;
- rendering of booking information for participants in different timezones.

## Quality objectives

The engagement is designed to answer these questions, in order:

1. Does the same intended instant remain correct across host, booker, API,
   persisted data, confirmation page, and notification?
2. Can concurrent users create more bookings than the slot capacity permits?
3. Do rescheduling and cancellation update every observable representation of a
   booking without leaving stale availability or notifications?
4. Can a user see or modify availability and booking information they do not own?
5. Can a keyboard or assistive-technology user complete the public booking flow?
6. Does the self-hosted snapshot remain usable under a measured, local workload?

## Risk model

Likelihood and impact are scored from 1 (low) to 5 (very high). The score is
`likelihood × impact`; it determines implementation order, not defect severity.
A rare data-integrity failure may still be a critical defect.

| Priority | Risk | Likelihood | Impact | Score | Primary evidence |
|---:|---|---:|---:|---:|---|
| 1 | Timezone or DST conversion changes the intended booking instant | 4 | 5 | 20 | API boundaries plus timezone-focused E2E |
| 2 | Concurrent requests overbook a capacity-one slot | 3 | 5 | 15 | API concurrency test and k6 contention gate |
| 3 | Reschedule or cancellation leaves inconsistent state | 3 | 4 | 12 | API lifecycle tests, E2E, mail assertions |
| 4 | Confirmation or lifecycle notification is missing or wrong | 3 | 4 | 12 | Mailpit assertions correlated by booking ID |
| 5 | Availability or booking data leaks across users | 2 | 5 | 10 | Authentication and authorization negatives |
| 6 | Public booking flow is inaccessible | 3 | 3 | 9 | axe-core plus keyboard journey |
| 7 | Availability or booking latency degrades under load | 3 | 3 | 9 | k6 thresholds calibrated to local Docker |

Timezone and DST rank above payments because time conversion is intrinsic to
every booking in this target, while real payment-provider integration is outside
the controlled environment and would introduce third-party credentials and
behavior. That is a scope decision, not a claim that payments are low risk.

The detailed failure model for priority 1 is in `docs/RISK-ANALYSIS.md`.

## Test levels and ownership

| Level | Ownership in this engagement | Boundary |
|---|---|---|
| Upstream unit tests | Cal.diy maintainers | Read as context; not copied or counted as portfolio coverage |
| API and integration | This repository, Phase 2 | Public API v2 behavior, persistence-visible outcomes, auth, schema, cleanup |
| Browser E2E | This repository, Phase 3 | A small set of high-value journeys and timezone presentation |
| BDD acceptance | This repository, Phase 3 | Business-readable booking, reschedule, and cancel scenarios only |
| Accessibility and visual | This repository, Phase 3 | Public booking surface across agreed viewports |
| Performance | This repository, Phase 4 | Availability reads and booking contention in local Docker |
| Observability and reporting | This repository, Phase 5 | Allure evidence and longitudinal TestPulse ingestion |

BDD does not wrap low-level API, boundary, schema, or visual tests. Step
definitions reuse the Playwright fixtures and page objects rather than
forming a second automation framework.

## Environments

### Local controlled environment

Phase 1 supplies Cal.diy, PostgreSQL, and Mailpit with immutable image digests.
The Phase 2 `api` profile adds the qualified local API v2 image and an
internal-only, digest-pinned Redis service. Web, Mailpit, and API HTTP ports bind
to loopback; PostgreSQL and Redis are not published to the host. Cal.diy
telemetry is disabled.

The environment is the reference for development and deterministic functional
checks. It is not a production topology, security baseline, or production SLO
environment.

### CI environment

GitHub Actions uses amd64 hosted Linux runners, the same controlled SUT commit,
and the same pinned database major version. Every live job starts an isolated
stack and creates independent data. Failure traces, screenshots, and videos are
retained for 14 days; merged reports and contract/performance evidence are
retained for 30 days. CI receives no credentials for hosted Cal.com, external
calendars, payments, or OAuth providers. Pull-request jobs cannot ingest
TestPulse history.

### Current-upstream confirmation — defect triage only

Before filing an upstream issue, a finding from `v6.2.0` must be searched for as
a duplicate and reproduced against the current public Cal.diy code. A finding
that exists only on this historical snapshot is documented locally as a
compatibility result, not filed as a current product defect.

## Test data strategy

- Bootstrap uses Cal.diy's official development seed. It does not insert custom
  SQL into an application schema owned by the SUT.
- `pro@example.com` and `/pro/30min` are the Phase 1 smoke fixtures. Their public
  development password is local test data, not a deployable secret.
- Phase 2 factories create prerequisites through supported APIs and register
  LIFO cleanup immediately after validated creation.
- Data names include the run and worker identity. No test may depend on
  another test's order, residue, or cleanup.
- Booking cleanup uses the supported cancellation endpoint; the product has no
  booking-delete endpoint. The guarded project reset removes retained local
  booking history when a clean database is required.
- Destructive reset is limited to the named Compose volumes and requires the
  literal confirmation `caldiy-qa-strategy`.
- Notification assertions query Mailpit and correlate a message to a unique
  booking identifier instead of assuming inbox order.

## Delivered tooling

Phase 2 delivers Python 3.12, pytest, httpx, xdist, a locked `uv` environment,
strict typing and linting, pinned timezone data, an unchanged OpenAPI snapshot,
JSON Schema validation, JUnit, coverage, and Allure-compatible raw results.
`docs/API-AUTOMATION.md` records its verified scope and local evidence.

Phase 3 delivers Playwright and TypeScript browser automation, exactly three
`@cucumber/cucumber` lifecycle journeys, axe-core accessibility checks, guarded
Chromium visual snapshots, and the pinned Python timezone oracle. Phase 4
delivers k6 availability, booking-throughput, and contention gates. Phase 5
delivers tiered GitHub Actions, merged Allure artifacts, and non-blocking
TestPulse ingestion for four stable suites. Phase 6 delivers current-main defect
auditing, professional defect reports, historical-finding triage, and eligible
public upstream issues.

API v2 remains absent from the default Phase 1 Compose stack. Its separate
profile was accepted after an exact-source local build and a ten-minute health
and memory qualification. The image is non-distributable and stays local.

## Entry and exit criteria

### Phase 1 entry

- Docker is available with an amd64 runtime.
- Ports 3000 and 8025 are free or explicitly overridden in `.env`.
- The pinned upstream image remains available by digest.

### Phase 1 exit

- A clean bootstrap reaches healthy PostgreSQL, Cal.diy, and Mailpit services.
- The official seed produces the public `/pro/30min` booking page.
- A second bootstrap skips the seed and preserves data.
- The guarded reset removes only the project volumes and rebuilds successfully.
- Static validation passes and both strategy documents contain no delivered-test
  or defect claims.
- Mohanad has written or approved the Phase 1 decision-log entries in his own
  words.

### Phase 2 exit

- The exact-source API v2 runtime passes its health, identity, stability, and
  memory qualification.
- All 18 used runtime operations match the unchanged pinned OpenAPI snapshot.
- Independent API tests cover the delivered positive and negative paths and
  emit JUnit, coverage, contract, and Allure-compatible evidence.
- The reusable JSON fixture CLI completes a create/destroy round trip.
- Local compatibility findings are versioned and are not presented as current
  upstream defects.
- Mohanad approves the Phase 2 decision-log entries before the closing commit.

### Phase 3 exit

- Chromium lifecycle coverage and focused Firefox smoke coverage pass without
  retries and clean their API-created prerequisites.
- Exactly three Cucumber journeys reuse the browser fixtures and page objects.
- The nine-zone matrix records exact UTC instants and pinned tzdata evidence,
  including gap, fold, fractional-offset, Cairo, and opposing-hemisphere cases.
- Axe findings remain blocking and unsuppressed; visual baselines are guarded,
  platform-specific, and pass ordinary comparison on their source platform.
- Snapshot-only observations are not filed as current defects without current
  reproduction.

### Phase 4 exit

- Five complete local baseline runs calibrate the availability threshold using
  the declared formula, and the value is labeled as a local Docker threshold.
- Availability and unique-booking workloads stay below the non-contention error
  gate and clean their active resources.
- Twenty-way contention produces exactly one successful and one persisted
  capacity-one booking, with expected conflicts reported separately.
- Threshold outcomes produce honest JUnit cases while detailed k6 distributions
  and environment metadata remain artifacts.

### Phase 5 exit

- Pull-request, push, and nightly/manual tiers enforce their documented scope;
  four Playwright blobs merge exactly once.
- Failure evidence, merged reports, and Allure output follow the 14/30-day
  retention policy, and Pages remains explicitly gated until public release.
- TestPulse secret checks reveal presence only; eligible reports use four stable
  suite names and ingestion cannot change product confidence.
- The flaky-test policy names the owner, quarantine evidence/expiry, and return
  criteria. No current test is quarantined or retried.

### Phase 6 exit

- Every historical finding has a current disposition without manufacturing a
  current defect from snapshot-only evidence.
- Filed reports include exact commit, duplicate search, steps, impact boundary,
  evidence, and labeled root-cause inference.
- Public issues link back to the professional reports, and hosted Cal.com remains
  explicitly untested.
- Mohanad approves the final decision statements before the closing commit.

Every phase retains the same rule: passing evidence, independent rerunability,
truthful status, and an approved decision-log update are required before its
checkpoint is closed. Test counts come from run artifacts, never estimates.

## Reporting and defect policy

Every reported defect must include target commit, environment, preconditions,
minimal reproduction, expected and actual behavior, severity rationale, and
evidence. Suspected root cause is optional and must be labeled as a hypothesis.

No bug will be manufactured to improve the portfolio. A suite finding no defect
is reported with the cases and version tested. Upstream issues are created only
for findings that are current, reproducible, searched for duplicates, and
appropriate for the public Cal.diy repository.

Flaky tests are not silently retried into green. CI records the first failure,
retains traces, and permits a time-limited quarantine only after evidence
supports a test-flake classification. The suites emit genuine JUnit and
Allure-compatible results. Phase 5 verified TestPulse ingestion from `main` and
manual history; the earlier local-only Phase 2 run is not retroactively
ingested.

## Explicit exclusions

- current hosted Cal.com behavior or private source code;
- enterprise-only organizations, SSO/SAML, billing, or support promises;
- live Stripe, PayPal, Google Calendar, Microsoft, Zoom, or other provider
  credentials;
- native mobile applications;
- email deliverability beyond Cal.diy handing a message to local SMTP;
- destructive penetration testing, denial-of-service testing, or public-host
  load generation;
- production capacity or availability SLO claims.

These exclusions can be revisited only by a documented decision with a safe,
reproducible environment and a truthful change to the project claims.
