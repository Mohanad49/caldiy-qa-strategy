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
