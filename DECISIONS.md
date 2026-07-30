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

## Phase 1 prompts — awaiting Mohanad

Write or approve entries covering these decisions:

1. Why the target changed from Cal.com to the `v6.2.0` snapshot now published
   as Cal.diy, and why keeping the old project wording would be misleading.
2. Why the QA engagement is a standalone repository using an immutable image
   rather than a fork or vendored copy of the large upstream monorepo.
3. Why Phase 1 stops at environment and strategy instead of scaffolding empty
   API, E2E, BDD and performance suites.
4. Why the official development seed is used instead of direct custom SQL.
5. Why browser clock emulation alone is insufficient for deterministic DST
   coverage.
6. Why API v2 and TestPulse integration are deferred until genuine test output
   exists.

Phase 1 remains incomplete until these entries are written or approved.
