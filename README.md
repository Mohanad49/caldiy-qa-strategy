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
| 1 | Pinned local environment, test strategy, risk analysis | In progress |
| 2 | API v2 automation with pytest and httpx | Planned |
| 3 | Playwright E2E, selective Cucumber BDD, accessibility and visual checks | Planned |
| 4 | k6 performance and contention gates | Planned |
| 5 | CI, Allure reporting and TestPulse ingestion | Planned |
| 6 | Verified defect reports and eligible upstream reports | Planned |

There are currently no automated product tests, performance results, defect
claims, or upstream issues in this repository.

## Phase 1 commands

The command interface is added with the pinned environment during Phase 1:

```text
make sut-bootstrap
make sut-smoke
make sut-down
make sut-reset CONFIRM=caldiy-qa-strategy
make validate
```

## Local fixture boundary

Cal.diy's official development seed provides accounts such as
`pro@example.com` / `pro`. These are public, local-only fixture credentials.
They must never be reused for a deployed environment or treated as secrets.

## Documentation

- `docs/TEST-STRATEGY.md` — engagement scope, risk priorities and quality gates
- `docs/RISK-ANALYSIS.md` — timezone and DST failure model
- `DECISIONS.md` — decisions written or approved by Mohanad after each phase
