# Cal.diy QA Strategy & Automation

A risk-led QA engagement against the self-hostable Cal.diy scheduling platform.
The project begins with the test environment and strategy; automation is added
only after the risks and test boundaries are explicit.

## Target provenance

The system under test is the public [`calcom/cal.diy`](https://github.com/calcom/cal.diy)
repository at tag [`v6.2.0`](https://github.com/calcom/cal.diy/releases/tag/v6.2.0),
commit `1c193cca8682b33b9866c792186033f7ef886682`. That tag was published while the
repository still carried the Cal.com name. In April 2026, Cal.com moved its
production codebase to a private repository and renamed the public repository
Cal.diy. This engagement therefore does **not** claim access to, or coverage of,
the current hosted Cal.com production code. The vendor's transition is described
in its [announcement](https://cal.com/blog/cal-com-goes-closed-source-why).

## Delivery status

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Pinned local environment, test strategy, risk analysis | Implemented |
| 2 | API v2 automation with pytest and httpx | Implemented |
| 3 | Playwright E2E, selective Cucumber BDD, accessibility and visual checks | Implemented |
| 4 | k6 performance and contention gates | Implemented |
| 5 | CI, Allure reporting and TestPulse ingestion | Planned |
| 6 | Verified defect reports and eligible upstream reports | Planned |

The Phase 2 local run passed 13 of 13 API tests in 17.58 seconds with 77%
branch-aware package coverage. It produced 14 evidence-backed contract
compatibility findings against the historical `v6.2.0` snapshot.

Phase 3 produced these local results: 12 of 12 browser lifecycle tests passed,
all three BDD scenarios and 18 steps passed, 13 of 13 timezone tests passed,
and both visual comparisons passed. The accessibility gate intentionally
remains red: one of three surfaces passed and two failed with three documented
serious or critical findings. The timezone suite produced one additional local
snapshot finding. These are local results, not current-upstream or hosted
Cal.com claims; none has been filed upstream.

Phase 4 established a five-run local availability baseline and a 2,300 ms p95
gate. The commit-bound acceptance run passed at 1,408.838 ms p95 with zero
application errors across 924 measured calls. The throughput run completed 50
of 50 unique bookings with zero application or cleanup errors. Twenty-way
contention produced exactly one success, 19 expected conflicts, and one
persisted booking, with zero unexpected, persistence, or cleanup errors. These
are local amd64 Docker results, not production SLOs or public-infrastructure
load results.

[TestPulse](https://github.com/Mohanad49/testpulse) is already a separate,
publicly available project. Only this repository's report ingestion into
TestPulse remains planned.

## Stable commands

Phase 1 environment commands:

```text
make sut-bootstrap
make sut-smoke
make sut-down
make sut-reset CONFIRM=caldiy-qa-strategy
make validate
```

Phase 2 API runtime and automation commands:

```text
make api-build
make sut-api-bootstrap
make sut-api-smoke
make test-bootstrap
make test-api
make contracts-verify
```

Phase 3 browser, timezone and accessibility commands:

```text
make test-e2e
make test-timezones
make test-bdd
make test-a11y
make update-snapshots CONFIRM=caldiy-qa-strategy
```

Phase 4 local performance commands:

```text
make perf-baseline
make test-perf
make test-contention
```

The API v2 image is built locally from the exact controlled commit and is not
redistributable. It must not be pushed to a container registry.

## Local fixture boundary

Cal.diy's official development seed provides accounts such as
`pro@example.com` / `pro`. These are public, local-only fixture credentials.
They must never be reused for a deployed environment or treated as secrets.

## Documentation

- `docs/TEST-STRATEGY.md` — engagement scope, risk priorities and quality gates
- `docs/RISK-ANALYSIS.md` — timezone and DST failure model
- `docs/API-V2-RUNTIME.md` — exact-source build and runtime qualification evidence
- `docs/API-AUTOMATION.md` — client design, contract policy, coverage and local results
- `docs/PHASE-3-EVIDENCE.md` — measured browser, timezone, accessibility and visual results
- `docs/PHASE-4-EVIDENCE.md` — measured local performance and contention results
- `docs/findings/` — snapshot-specific compatibility findings requiring current-upstream verification
- `DECISIONS.md` — decisions written or approved by Mohanad after each phase
