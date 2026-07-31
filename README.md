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
| 3 | Playwright E2E, selective Cucumber BDD, accessibility and visual checks | Planned |
| 4 | k6 performance and contention gates | Planned |
| 5 | CI, Allure reporting and TestPulse ingestion | Planned |
| 6 | Verified defect reports and eligible upstream reports | Planned |

The Phase 2 local run passed 13 of 13 API tests in 17.58 seconds with 77%
branch-aware package coverage. It produced 14 evidence-backed contract
compatibility findings against the historical `v6.2.0` snapshot. These are
local results, not CI or current-upstream claims; no upstream issue has been
filed. Browser, timezone-transition, accessibility, visual, BDD and performance
results remain planned.

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
- `docs/findings/` — snapshot-specific compatibility findings requiring current-upstream verification
- `DECISIONS.md` — decisions written or approved by Mohanad after each phase
