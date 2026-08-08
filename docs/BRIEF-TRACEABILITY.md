# Project brief traceability

This matrix maps the original portfolio brief to delivered evidence. The brief
predates Cal.com's April 2026 source transition, so its product name and several
implementation assumptions required correction. Those corrections narrow the
claims; they do not imply access to current hosted Cal.com.

| Brief area | Delivered evidence | Boundary or deliberate deviation |
|---|---|---|
| Phase 1 environment | Digest-pinned Compose stack, one-command bootstrap, idempotent official seed, guarded reset, smoke checks | Targets Cal.diy `v6.2.0`, the final public Cal.com snapshot, rather than current hosted Cal.com |
| Phase 1 strategy | [Test strategy](TEST-STRATEGY.md), risk scoring, levels, data isolation, entry/exit criteria and exclusions | Payments remain risk-ranked but unexecuted because real providers and credentials are outside the controlled environment |
| Phase 1 DST analysis | [Timezone/DST risk analysis](RISK-ANALYSIS.md) written before the tests | Playwright Clock is limited to browser-side time; it cannot freeze the server or database |
| Phase 2 API | 13 independent pytest/httpx cases covering identity, authorization, event types, schedules, slots and booking lifecycle | API-key and invalid-bearer behavior are covered; full OAuth-provider setup is explicitly out of scope |
| Phase 2 negative boundaries | Malformed/missing payloads, invalid zones, past and outside-availability bookings, not found, cross-owner access and same-slot conflict | Undocumented error responses use a committed common envelope and remain reported contract omissions |
| Phase 2 contracts | Canonical OpenAPI snapshot with verified hash; 18 used runtime operations must match it exactly | Current public `main` is a moving advisory, not a failing gate, because the controlled SUT is intentionally historical |
| Phase 2 data isolation | Run/worker-aware builders, LIFO supported-interface cleanup and `caldiy-fixtures create|destroy --json` | Cancelled booking history is removed only by the project-scoped reset because API v2 exposes cancellation, not deletion |
| Phase 3 core browser flows | Signup when enabled, login, UI event-type creation, availability editing, guest booking, reschedule, cancel and Mailpit correlation | Initial local booking emits an organizer action-required message without external calendar credentials; no guest confirmation is invented |
| Phase 3 browser architecture | Playwright fixtures, page objects, API-created prerequisites, isolated guest contexts, Chromium authority and Firefox lifecycle smoke | Exactly three stakeholder-readable Cucumber journeys; contracts, DST, axe and visuals stay in native layers |
| Phase 3 timezone/DST | 14 tests across UTC, New York, London, Cairo, Kolkata, Kathmandu, Eucla, Sydney and Phoenix, backed by pinned Python `zoneinfo` | Historical Cairo and unavailable crossing-slot states are recorded as product limitations rather than created through SQL |
| Phase 3 accessibility/visuals | Three unsuppressed axe surfaces and two guarded Chromium snapshots at desktop/mobile viewports | The axe gate remains red for evidence-backed snapshot findings; screenshots are platform-specific because text rasterization differs |
| Phase 4 availability | Five-run local baseline, 20-VU/60-second gate and retained k6 distributions/metadata | The measured gate is 2,300 ms, not the brief's uncalibrated 500 ms; it is a local Docker threshold, never a production SLO |
| Phase 4 throughput/contention | 50 unique booking lifecycles; 20 synchronized requests require exactly one success and one persisted booking | Expected conflict responses are separated from transport/application errors |
| Phase 4 reporting | Honest JUnit threshold cases under `caldiy-performance-gates`; k6 detail retained as artifacts | TestPulse stores gate history, not synthetic percentile test cases |
| Phase 5 CI | PR, push and nightly/manual tiers; four Playwright shards merged once; bounded jobs; retained failure/report artifacts | The non-redistributable API image is rebuilt from source and cached as layers only |
| Phase 5 reporting | Merged Allure artifact and four stable TestPulse suite names | Pages activation is intentionally deferred until the owner changes the repository to public; [the release checklist](PUBLIC-RELEASE.md) records the exact step |
| Phase 5 flake policy | No retries or quarantines; evidence, owner, expiry and same-commit return criteria are documented | Accessibility violations, conflicts and infrastructure incidents cannot be relabeled as flakes merely because a rerun passes |
| Phase 6 defects | Historical finding register, current-commit audit, duplicate searches, two professional reports and public issues [#29903](https://github.com/calcom/cal.diy/issues/29903) and [#29904](https://github.com/calcom/cal.diy/issues/29904) | Snapshot-only findings stay local; hosted Cal.com was not tested |
| Cross-cutting constraints | Python owns API/oracle work; TypeScript owns browser work; shared JSON fixture boundary; small unsquashed commits | No test depends on another test's state; retained evidence is ignored locally or stored as bounded CI artifacts |
| Portfolio publication | README case study, Mermaid architecture, four owner-approved public TestPulse summaries and publicly verifiable upstream issues | No CI badge while the enforced historical-snapshot accessibility gate is red; Allure Pages remains an owner-controlled post-visibility step |

## Public-release remainder

All repository implementation is present. The only deliberately unexecuted
brief item is public Allure Pages publication because the repository is still
private by owner choice. Visibility, Pages enablement and the first publication
are owner-controlled release operations, not test-suite code changes.
