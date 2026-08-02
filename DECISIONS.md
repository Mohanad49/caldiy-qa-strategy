# Decision Log

This file records why the project was built this way. It is deliberately not a
generated architecture summary. Mohanad must write or explicitly approve each
entry in his own words before the corresponding phase is complete.

## Entry format

### D-XXX — Short decision title

- **Status:** Proposed | Accepted | Revisited
- **Context:** What forced a choice?
- **Decision:** What did I choose?
- **Rejected alternative:** What did I not choose, and why?
- **Consequences:** What becomes easier, harder, or deliberately deferred?
- **Evidence:** What did I run, read, or observe?

## Phase 1 decisions

Mohanad approved the six **Decision** statements on 2026-07-31. The surrounding
context, consequences, and evidence record the Phase 1 implementation.

### D-001 — Test the public Cal.diy snapshot

- **Status:** Accepted
- **Context:** Current Cal.com production source is private; the final public
  release is now published in the Cal.diy repository.
- **Decision:** I changed the target from “Cal.com” to the public Cal.diy
  `v6.2.0` snapshot because current Cal.com production code is private, and
  keeping the old wording would overstate what I tested.
- **Rejected alternative:** Keep the original Cal.com label or imply coverage
  of the current hosted product.
- **Consequences:** Findings and coverage claims apply only to tag `v6.2.0`,
  commit `1c193cca8682b33b9866c792186033f7ef886682`.
- **Evidence:** Cal.com's transition announcement, the public repository, and
  the tagged release and commit.

### D-002 — Keep the QA engagement standalone

- **Status:** Accepted
- **Context:** The engagement owns QA strategy and evidence, while Cal.diy is a
  large upstream application maintained elsewhere.
- **Decision:** I used a standalone QA repository and immutable upstream image
  because the engagement owns test strategy and evidence, not a modified copy
  of the Cal.diy monorepo.
- **Rejected alternative:** Fork or vendor the upstream monorepo without a
  product-code change to justify maintaining that copy.
- **Consequences:** The SUT stays traceable by tag, commit, and image digest;
  this repository remains focused on test assets and evidence.
- **Evidence:** The pinned Compose configuration and the repository's
  incremental Phase 1 commit history.

### D-003 — Build evidence before suite scaffolding

- **Status:** Accepted
- **Context:** Phase 1 needed a reproducible target and explicit risk model
  before choosing suite structure.
- **Decision:** I stopped Phase 1 at environment and strategy because empty API,
  E2E, BDD, and performance scaffolds would create activity without test
  evidence.
- **Rejected alternative:** Create empty automation directories and report
  framework setup as progress.
- **Consequences:** Later phases must add only implemented, runnable tests and
  keep their delivery status planned until evidence exists.
- **Evidence:** The Phase 1 status table, strategy exit criteria, and absence of
  empty automation suites.

### D-004 — Seed through the SUT's supported tooling

- **Status:** Accepted
- **Context:** Cal.diy owns its database schema and bundles an official
  development seed.
- **Decision:** I used Cal.diy’s official development seed because direct SQL
  would couple the project to an application schema it does not own.
- **Rejected alternative:** Insert fixture users and event types directly into
  PostgreSQL.
- **Consequences:** Bootstrap follows upstream behavior and checks for
  `pro@example.com` before seeding to remain idempotent.
- **Evidence:** Clean bootstrap, repeated bootstrap, preserved-state restart,
  confirmed reset, and `/pro/30min` smoke results.

### D-005 — Control both browser and server-side time assumptions

- **Status:** Accepted
- **Context:** DST behavior crosses browser, application, database, and
  timezone-data boundaries.
- **Decision:** I will not rely on Playwright Clock alone for DST testing
  because it controls browser time but does not freeze Cal.diy’s server,
  database, or container clocks.
- **Rejected alternative:** Treat browser clock emulation as a deterministic
  end-to-end time control.
- **Consequences:** Later tests will combine browser timezone controls, explicit
  UTC instants, and an independently pinned timezone oracle.
- **Evidence:** The Phase 1 timezone and DST risk analysis.

### D-006 — Defer integrations until their runtime and evidence are real

- **Status:** Accepted
- **Context:** The local Docker allocation is 8 GB, API v2's upstream build
  reserves an 8 GB Node heap, and this repository does not yet emit test reports.
- **Decision:** I deferred API v2 until its runtime fits reliably within the
  8 GB Docker allocation, and deferred Cal.diy-to-TestPulse ingestion until
  genuine test reports exist.
- **Rejected alternative:** Add an unverified API v2 service or send fabricated
  placeholder results to the existing public TestPulse project.
- **Consequences:** Phase 2 must validate an API v2 runtime first; TestPulse
  remains operational independently and will receive Cal.diy data only after
  real reports are produced.
- **Evidence:** The API v2 build's memory requirement, the local Docker resource
  limit, and the public `Mohanad49/testpulse` repository.

## Phase 2 decisions

Mohanad approved the five **Decision** statements on 2026-07-31. The surrounding
context, consequences, and evidence record the Phase 2 implementation.

### D-007 — Keep the API v2 image private and local

- **Status:** Accepted
- **Context:** The historical API v2 package is marked `UNLICENSED` and private
  in the controlled source snapshot.
- **Decision:** I built API v2 from the exact public `v6.2.0` commit for private
  testing only, and I will not publish its local image because upstream marks
  the package `UNLICENSED`.
- **Rejected alternative:** Push the qualified image to Docker Hub, GHCR, or
  another registry for reuse.
- **Consequences:** Each permitted environment must rebuild from the verified
  source commit; the large local image is test infrastructure, not a project
  deliverable.
- **Evidence:** The exact source verifier, pinned builder, non-redistributable
  image label, and accepted local image metadata in `docs/API-V2-RUNTIME.md`.

### D-008 — Bound the historical license exception

- **Status:** Accepted
- **Context:** Upstream documents a fixed local `Deployment` record, while the
  historical external license endpoint returns HTTP 404 for that zero key.
- **Decision:** I used upstream's documented local `Deployment` record and
  `IS_E2E` runtime switch because the historical license endpoint returns 404;
  license and billing enforcement remain outside this engagement.
- **Rejected alternative:** Invent a replacement license service, silently fall
  back to API v1, or treat a broken license check as a product test result.
- **Consequences:** API behavior can be tested locally, but this environment
  provides no evidence about commercial licensing or billing controls.
- **Evidence:** The idempotent deployment bootstrap, observed 404 response, API
  source behavior, and qualified `/health`, `/docs-json`, and `/v2/me` checks.

### D-009 — Preserve the canonical contract and expose deviations

- **Status:** Accepted
- **Context:** The pinned OpenAPI document contains reproducible schema defects,
  but rewriting it would hide what the controlled release actually publishes.
- **Decision:** I kept the canonical OpenAPI snapshot unchanged and use narrow,
  evidence-backed projections only after original validation fails, so the
  suite does not silently rewrite upstream contracts.
- **Rejected alternative:** Patch the stored OpenAPI document, disable response
  validation, or accept arbitrary mismatches.
- **Consequences:** Known deviations remain visible in test warnings and
  reports; any unknown schema mismatch still fails its test.
- **Evidence:** The verified snapshot hash, exact comparison of 18 used runtime
  operations, common error-envelope policy, and 14 local compatibility reports.

### D-010 — Clean through supported interfaces

- **Status:** Accepted
- **Context:** Cal.diy API v2 supports booking cancellation but does not expose
  booking deletion, while schedules and event types can be deleted.
- **Decision:** I clean test resources through supported endpoints in LIFO
  order; bookings are cancelled rather than deleted, and the guarded project
  reset clears retained local history at the checkpoint.
- **Rejected alternative:** Delete application rows directly during each test
  or claim that cancellation removes booking history.
- **Consequences:** Tests leave no active bookable resource, cleanup failures
  remain visible, and the project-scoped volume reset is required to return the
  database to official fixtures only.
- **Evidence:** Factory cleanup manifests, the CLI create/destroy round trip,
  post-run residue audit, and successful guarded reset and reseed.

### D-011 — Report only the evidence this phase produced

- **Status:** Accepted
- **Context:** Phase 2 generated local API evidence, while tiered CI and
  TestPulse ingestion belong to Phase 5.
- **Decision:** I report only the real local 13-test JUnit run in Phase 2; I will
  not claim API CI execution or TestPulse history until Phase 5 produces them.
- **Rejected alternative:** Treat repository static validation as API-suite CI
  evidence or ingest placeholder results into TestPulse.
- **Consequences:** The README can state the measured local result and contract
  findings, but no CI badge, longitudinal trend, or cross-browser claim appears
  yet.
- **Evidence:** The 13-of-13 local run, 17.58-second JUnit result, 77% coverage,
  generated local report formats, and absence of TestPulse ingestion.

## Phase 3 decisions

Mohanad approved the seven **Decision** statements on 2026-08-01. The
surrounding context, consequences, and evidence record the Phase 3
implementation.

### D-012 — Split browser authority by purpose

- **Status:** Accepted
- **Context:** Timezone emulation and deterministic screenshots need one stable
  browser target, while the main booking lifecycle still needs a second-engine
  compatibility signal.
- **Decision:** I made Chromium authoritative for lifecycle, timezone,
  accessibility and visual coverage, and use Firefox only for focused lifecycle
  smoke coverage because duplicating every matrix across browsers would add
  runtime without equivalent risk coverage.
- **Rejected alternative:** Run every timezone, accessibility and visual case
  in both Chromium and Firefox.
- **Consequences:** Chromium failures govern these Phase 3 gates; Firefox can
  reveal lifecycle incompatibilities but does not establish visual or timezone
  parity.
- **Evidence:** The 12-test lifecycle run, 13-test timezone run, three-surface
  axe run, and two Chromium visual comparisons.

### D-013 — Keep Gherkin selective

- **Status:** Accepted
- **Context:** Gherkin helps stakeholders read complete user journeys but makes
  lower-level matrices and contract assertions harder to maintain.
- **Decision:** I use Cucumber for exactly three journeys—booking,
  rescheduling, and cancellation—and keep API contracts, timezone matrices,
  accessibility, and visual checks in their native test layers.
- **Rejected alternative:** Wrap every automated check in Gherkin or omit BDD
  completely.
- **Consequences:** The feature file stays readable and reuses the Playwright
  fixture and page-object layer without duplicating test infrastructure.
- **Evidence:** One feature containing three scenarios and 18 passing steps,
  plus the Phase 3 static scenario-count contract.

### D-014 — Use an independent timezone oracle

- **Status:** Accepted
- **Context:** Browser time controls do not freeze Cal.diy's server, database,
  or container clocks, and DST expectations must not be derived from the SUT.
- **Decision:** I generate expected transitions and UTC instants with Python
  `zoneinfo` forced to pinned `tzdata==2026.3`; browser `timezoneId` controls
  rendering, and Playwright Clock is limited to browser-side “now” behavior.
- **Rejected alternative:** Treat Playwright Clock as an end-to-end server time
  control or calculate expected offsets with Cal.diy itself.
- **Consequences:** Results record explicit UTC instants and tzdata versions,
  while tests separately verify that browser clock control did not freeze the
  server.
- **Evidence:** The 13-of-13 transition matrix and attached oracle records for
  nine named zones.

### D-015 — Preserve the real notification boundary

- **Status:** Accepted
- **Context:** The local fixture has no external calendar credentials, so an
  initial booking emits Cal.diy's organizer `[Action Required] Confirmed`
  message instead of the normal guest confirmation.
- **Decision:** I correlate the organizer notification for initial booking and
  the guest lifecycle messages for rescheduling and cancellation, and document
  the missing initial guest message as an environment limitation instead of
  manufacturing a confirmation path.
- **Rejected alternative:** Claim a guest confirmation that was not emitted,
  weaken email correlation, or introduce external calendar credentials into
  the controlled local fixture.
- **Consequences:** Notification evidence is truthful but does not establish
  normal guest-confirmation behavior for a calendar-connected deployment.
- **Evidence:** Correlated Mailpit assertions in the Playwright and Cucumber
  lifecycle runs.

### D-016 — Keep the accessibility gate red

- **Status:** Accepted
- **Context:** Axe found serious or critical failures on two of three tested
  surfaces in the controlled snapshot.
- **Decision:** I keep the accessibility gate failing and record the findings
  with affected nodes; I do not suppress rules or exclude regions merely to
  produce a green result.
- **Rejected alternative:** Disable the failing axe rules, lower the impact
  threshold, or report the suite as passing.
- **Consequences:** Phase 3 has an honest red quality signal and three local
  findings that require current-upstream reproduction before filing.
- **Evidence:** `CALDIY-LOCAL-002` through `CALDIY-LOCAL-004`, their attached
  JSON evidence, and the stable one-pass/two-fail accessibility run.

### D-017 — Guard visual baseline changes

- **Status:** Accepted
- **Context:** Booking dates and time choices vary with generated fixtures, but
  broad masks would make layout regressions invisible.
- **Decision:** I mask only the proven dynamic calendar regions and require
  `CONFIRM=caldiy-qa-strategy` before updating the two committed Chromium
  baselines.
- **Rejected alternative:** Auto-update snapshots, mask the complete calendar,
  or omit dynamic controls and accept date-driven churn.
- **Consequences:** Reviews retain layout evidence at 1440×900 and 390×844;
  baseline changes are explicit and ordinary comparison cannot overwrite them.
- **Evidence:** The refused unconfirmed update, confirmed update, clean ordinary
  comparison, and exact PNG dimension checks in repository validation.

### D-018 — Keep snapshot findings local until current reproduction

- **Status:** Accepted
- **Context:** Phase 3 exercises a historical Cal.diy release and found one
  repeated-hour behavior plus three accessibility failures.
- **Decision:** I classify these as local snapshot findings only; I will not
  call them current Cal.diy defects or file them upstream until Phase 6 repeats
  them against current Cal.diy and searches for duplicates.
- **Rejected alternative:** File issues directly from the historical snapshot
  or imply that hosted Cal.com has the same behavior.
- **Consequences:** The evidence remains useful without overstating product
  currency; a finding can be closed as historical compatibility evidence if it
  no longer reproduces.
- **Evidence:** `CALDIY-LOCAL-001` through `CALDIY-LOCAL-004` and the explicit
  provenance boundary in each report.

## Phase 4 decisions

Mohanad approved the five **Decision** statements on 2026-08-03. The surrounding
context, consequences, and evidence record the Phase 4 implementation.

### D-019 — Preserve the real local traffic controls

- **Status:** Accepted
- **Context:** The official seed API key is limited to 120 requests per minute,
  while public slot discovery can identify independent callers without an API
  key.
- **Decision:** I preserve Cal.diy's tracked rate-limit behavior: availability
  uses a distinct public client ID per virtual user, authenticated scenarios
  wait for the official seed key's real budget, and the harness does not change
  Redis, database, or runtime rate-limit state to make a run pass.
- **Rejected alternative:** Flush Redis, insert a rate-limit override, or run
  authenticated load fast enough to measure throttling instead of the intended
  booking behavior.
- **Consequences:** Authenticated scenarios are deliberately bounded and can
  wait for a budget reset; their throughput is a local functional gate rather
  than a maximum-capacity benchmark.
- **Evidence:** The budget preflight, 120-request-per-minute observation, local
  target contract, and accepted runs without a rate-limit override.

### D-020 — Calibrate from the worst complete baseline run

- **Status:** Accepted
- **Context:** A single workstation run is noisy, and a local Docker threshold
  cannot establish a production objective.
- **Decision:** I set the availability gate to the larger of 500 ms or 125% of
  the worst p95 across five complete baseline runs, rounded up to 50 ms, and I
  describe the resulting 2,300 ms value as a local amd64 Docker threshold—not a
  production SLO.
- **Rejected alternative:** Select the fastest or average run, invent a round
  threshold before measurement, or present workstation latency as a production
  promise.
- **Consequences:** One slower but valid baseline run influences the gate;
  recalibration requires another complete five-run evidence set on a controlled
  environment.
- **Evidence:** Five zero-error p95 values of 894.964, 1,811.045, 705.000,
  1,003.723, and 535.255 ms and the checked-in formula result.

### D-021 — Keep throughput data functionally independent

- **Status:** Accepted
- **Context:** Reusing a slot or attendee would turn expected booking conflicts
  into apparent transport/application failures and would not measure the
  intended booking path.
- **Decision:** I use 50 unique slots and attendee identities for booking
  throughput, cancel every successful booking through the supported API, and
  fail the gate on any application or cleanup error.
- **Rejected alternative:** Rebook the same slot, share attendees across
  iterations, exceed the seed key's known budget, or delete application rows
  directly.
- **Consequences:** The workload exercises independent booking lifecycles and
  stays within the real local API boundary; cancelled history is removed only
  by the guarded project reset.
- **Evidence:** The 50-of-50 accepted run, zero application and cleanup errors,
  supported cancellations, and successful checkpoint reset.

### D-022 — Gate contention on both response and persistence invariants

- **Status:** Accepted
- **Context:** Response counts alone cannot prove that only one booking was
  persisted for a capacity-one slot, and generic k6 HTTP failure metrics count
  expected conflict statuses as failures.
- **Decision:** I require exactly one successful response, 19 expected conflict
  responses, and exactly one persisted booking for the targeted event and
  instant, while separately requiring zero unexpected, persistence, and cleanup
  errors.
- **Rejected alternative:** Accept any mix of non-2xx responses, infer database
  integrity only from HTTP 201 counts, or fail the scenario merely because k6
  classifies expected HTTP 400/409 conflicts as generic HTTP failures.
- **Consequences:** A duplicate response or persisted booking is a critical
  integrity failure; expected conflicts remain visible without being confused
  with transport errors.
- **Evidence:** The accepted 20-way run produced 1 success, 19 conflicts, 1
  persisted booking, and zero errors in all three negative counters.

### D-023 — Convert only honest gate outcomes to longitudinal test cases

- **Status:** Accepted
- **Context:** TestPulse can ingest JUnit test cases but does not currently model
  k6 latency distributions, and Phase 5 owns ingestion and retention policy.
- **Decision:** I convert only named k6 threshold outcomes into the stable
  `caldiy-performance-gates` JUnit suite, retain detailed latency distributions
  and environment metadata as k6 artifacts, and defer TestPulse ingestion until
  Phase 5.
- **Rejected alternative:** Turn every metric percentile into a synthetic test
  case, discard the raw distributions, or send Phase 4 results to TestPulse
  before the CI ingestion boundary exists.
- **Consequences:** Future longitudinal history has honest pass/fail semantics,
  while performance analysis still depends on retained k6 artifacts.
- **Evidence:** Four passing availability/throughput JUnit cases, six passing
  contention JUnit cases, gzip raw JSON, summaries, and commit-bound environment
  metadata.
