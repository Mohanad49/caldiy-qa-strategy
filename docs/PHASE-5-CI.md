# Phase 5 — Tiered CI and reporting

## Execution boundary

The workflow continues to exercise Cal.diy `v6.2.0` at commit
`1c193cca8682b33b9866c792186033f7ef886682`. It never targets hosted Cal.com or
public infrastructure. API v2 is rebuilt inside each permitted GitHub runner
from the exact source commit. Buildx reuses GitHub Actions cache layers, but the
`UNLICENSED` image is never pushed to a registry or uploaded as an artifact.
Because the workflow invokes Buildx from a shell script, it uses the
[Docker-documented runtime helper](https://docs.docker.com/build/cache/backends/gha/#authentication)
at an immutable commit to expose the cache service URL and token. The build
fails closed when those runtime variables are absent instead of silently
recompiling without the declared dependency cache.

The Buildx action boots an immutable BuildKit index at
`sha256:2f5adac4ecd194d9f8c10b7b5d7bceb5186853db1b26e5abd3a657af0b7e26ec`.
One annotated setup retry is permitted only when that pre-build infrastructure
step fails. Test execution, image compilation, contract validation, and product
assertions are never retried.

## Tiers

Pull requests run repository validation, a live API v2 smoke check, and the 18
used-operation contract comparison. They do not ingest TestPulse history.

Pushes to `main` add the complete API suite, four Playwright lifecycle shards,
exactly three Cucumber journeys, the unsuppressed accessibility gate, committed
visual comparisons, merged reports, and a static Allure artifact.

The nightly schedule and manual dispatch add the full pinned-oracle timezone
matrix, local-only k6 availability/booking/contention gates, a second isolated
API run against the same commit, and an informational comparison with the
current public Cal.diy `main` OpenAPI document. The current-upstream advisory
does not change the controlled SUT and does not claim coverage of hosted
Cal.com. To avoid starving the GitHub cache service with nine simultaneous
multi-gigabyte imports, the three manual-only SUT jobs begin after the core API
job; the proven six-consumer push fan-out remains unchanged.

## Sharding and report identity

Each of the four Playwright shards has its own SUT and emits only a blob report.
The merge job requires four blobs, then generates Playwright JSON, JUnit, and
Allure input once. TestPulse sees only that merged JSON, preventing four copies
of the same natural test key from entering history.

API, BDD, and k6 use JUnit. Performance conversion includes only declared k6
threshold outcomes; latency distributions remain in the retained k6 summaries
and raw gzip JSON. A duplicate-key rejecting JUnit merger combines the
availability/throughput and contention gate cases.

## Retention and Allure

Playwright blob reports, traces, screenshots, and video are retained for 14
days. Merged JUnit/JSON, API and BDD reports, k6 evidence, contract advisories,
raw Allure inputs, and the generated static Allure report are retained for 30
days. Allure CLI `2.43.0` is locked in the Node dependency graph.

The Pages deployment workflow is manual and additionally requires repository
variable `ENABLE_ALLURE_PAGES=true`. That variable is intentionally absent
while the repository is private, so Phase 5 cannot publish Pages.

## TestPulse boundary

Only `main`, scheduled, and manually dispatched runs can ingest these stable
suites:

- `caldiy-api-v2`
- `caldiy-e2e`
- `caldiy-bdd`
- `caldiy-performance-gates`

The action is pinned to TestPulse commit
`2696d715e7b18f2ef029e291f37371d6b4bb01fb`. It receives
`TESTPULSE_DATABASE_URL` only as a masked secret input. Secret checks emit only
a boolean presence output. Ingestion is `continue-on-error`: a TestPulse outage
cannot change product confidence, while the pinned action adds an error
annotation and workflow-summary failure record.

## Current evidence

Push-tier verification run
[`30778631910`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30778631910)
executed commit `9088b0d6c23ac81c2641848e9b2436aa450f1337` from the private
repository. Repository contracts, the warm cache prebuild, the 13-test API
suite, all four Playwright shards, the required four-blob merge, and the merged
Allure artifact succeeded. The API report contains 13 tests with zero failures;
the merged E2E report contains 15 tests with zero failures; and Cucumber
contains three scenarios with zero failures.

The browser-quality job failed and remains evidence, not noise. One of three
axe surfaces passed; the other two contain the already documented
serious/critical findings. Both visual comparisons failed because the committed
macOS baselines render text differently on the hosted Linux Chromium runner.
The Linux actual, expected, diff, trace, screenshot, and video files are
retained in the 14-day failure artifact. They are not promoted to baselines
without the guarded snapshot confirmation.

Run
[`30772862158`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30772862158)
proved the first authenticated cache export and exposed a test-isolation defect:
parallel Chromium and Firefox lifecycle tests selected the same organizer slot.
The tests now create non-overlapping schedule windows by journey and browser;
the two shards that failed in that run passed in `30778631910`.

The first authenticated cache export took 17 minutes 7 seconds. The next warm
prebuild took 1 minute 16 seconds. Consumer jobs showed Buildx steps 8 through
14 as `CACHED`, loaded the 8,192 MB-heap image locally, and never published it.

Manual-tier run
[`30777108027`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30777108027)
proved the two-wave dependency on commit
`93eeeca6cf195025249c644ac707ba4d84642021`. The six core consumers started
between 01:34:56 and 01:35:03 UTC. The core API job passed at 01:44:21; only
then did timezone, repeated API, and k6 start at 01:44:24. Those three jobs all
passed, as did all four core Playwright shards, the four-blob merge, and both
API runs.

The manual-only evidence contains a 13-test pinned-oracle timezone matrix with
`tzdata==2026.3` and a second 13-test API run on the same commit. Hosted-runner
availability measured 320.39 ms p95 with 0/1,090 application errors against
the existing 2,300 ms local-Docker threshold. Booking throughput completed
50/50 with zero booking or cleanup errors. Contention produced one success, 19
expected conflicts, one persisted booking, and zero persistence or cleanup
errors. The merged performance JUnit contains ten passing threshold cases.

The same run compared 18 controlled operations with public Cal.diy `main` at
`038381aeca6261635357957d66b8ba85cdb29737`: nine were unchanged, nine changed,
and none was missing. This advisory is not evidence about hosted Cal.com.

The manual run's browser-quality results are not accepted as accessibility or
visual evidence. All three BDD, all three axe, and both visual cases received a
404 for freshly created booking routes. The retained trace proved the route
response, while the API fixtures themselves were created successfully. Commit
`9088b0d6c23ac81c2641848e9b2436aa450f1337` added a bounded 404-only route
readiness contract: it does not rerun scenarios or assertions, fails immediately
on any non-404 error, and records the observed status sequence on timeout. Push
run `30778631910` then restored the valid three-of-three BDD, one-of-three axe,
and zero-of-two visual pattern under the six-consumer fan-out.

Earlier manual run
[`30774902565`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30774902565)
was cancelled after its manual-only gates passed because nine concurrent cache
consumers starved a duplicate core API import for 19 minutes. That run exposed
the scheduling defect; `30777108027` is the runtime proof of the corrected
two-wave dependency. Neither red/cancelled run is described as a successful
overall workflow conclusion.

Manual verification run
[`30932432000`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30932432000)
confirmed `TESTPULSE_DATABASE_URL` by boolean presence only. The pinned action
completed successfully for the core API report, repeated same-commit API report,
once-merged E2E report, BDD report, and merged performance-gate report. Those
inputs use the four declared suite names; the two API ingestions intentionally
share `caldiy-api-v2` to create same-commit history rather than a fifth suite.

The same run remains red overall because the browser-quality job enforces the
known axe and hosted-Linux visual failures after evidence upload and BDD
ingestion. TestPulse is downstream of that product result. No database URL was
printed or copied, no CI badge is added, and no green workflow conclusion is
claimed.

`ENABLE_ALLURE_PAGES` remains absent, so Pages publication is disabled while
the repository is private. The repository remains private.

## Flaky-test policy

The repository has zero quarantined tests and configures no product-test
retries. A first failure is retained with its original trace, screenshot, video,
response, or k6 evidence; a later passing run does not erase it.

The repository maintainer, Mohanad, owns classification and quarantine. A test
may be called flaky only after the same commit is rerun in an isolated
environment and the evidence rules out a deterministic product failure. An
infrastructure outage, a real booking conflict, an accessibility violation, or
an undocumented contract response is not reclassified merely because a rerun
passes.

Any future quarantine requires a linked issue containing the evidence, named
owner, narrow test identity, reason, and an expiry no later than 14 days. The
change must add a scheduled non-blocking execution path before the blocking
path may skip that test. An expired quarantine becomes blocking; it is not
silently extended.

A quarantined test returns to the blocking suite only after its root cause or
test defect is fixed and it passes three consecutive isolated runs of the same
commit. The linked issue records those run URLs. Repository validation must be
extended with any quarantine mechanism so an unowned or expired skip cannot be
merged.

## Known limitations

The private hosted runner must load a roughly 4.9 GB API image. An authenticated
prewarmed cache removes repeated compilation but still took roughly three to
ten minutes to restore/import in the observed fan-outs, before stack bootstrap.
In `30777108027`, the second-wave repeated API job took 17 minutes 35 seconds
end to end. This is a CI-efficiency limitation, not a production performance
result.
The workflow reclaims only the hosted image's unused Android SDK and records
disk usage before and after. Failure at either the upstream 8,192 MB heap or the
documented 6,144 MB OOM fallback remains a real CI infrastructure failure; the
workflow does not substitute API v1 or hosted Cal.com.

The Phase 4 2,300 ms availability threshold was calibrated on the controlled
amd64 Docker workstation. Nightly CI applies it as the existing local-Docker
gate, but the first hosted-runner evidence must be reviewed before describing
it as representative of that runner class. It remains explicitly not a
production SLO.

The historical snapshot has evidence-backed serious/critical accessibility
findings. The CI accessibility gate keeps those failures red; Phase 5 does not
suppress them to obtain a green workflow or badge.
