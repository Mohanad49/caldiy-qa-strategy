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

Push-tier run
[`30774193183`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30774193183)
executed commit `a2e0d3412aa31bab08ea54c7455206e4937f9ba8` from the private
repository. Repository contracts, the warm cache prebuild, the 13-test API
suite, all four Playwright shards, the required four-blob merge, and the merged
Allure artifact succeeded. The merged E2E report contains 15 tests with zero
failures; the API report contains 13 tests with zero failures; Cucumber contains
three scenarios with zero failures.

The browser-quality job failed and remains evidence, not noise. Axe reported
the two already documented serious/critical failures while the cancellation
panel passed. Both visual comparisons failed because the committed macOS
baselines render text differently on the hosted Linux Chromium runner. The
Linux actual, expected, diff, trace, screenshot, and video files are retained
in the 14-day failure artifact. They are not promoted to baselines without the
guarded snapshot confirmation.

Run
[`30772862158`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30772862158)
proved the first authenticated cache export and exposed a test-isolation defect:
parallel Chromium and Firefox lifecycle tests selected the same organizer slot.
The tests now create non-overlapping schedule windows by journey and browser;
the two shards that failed in that run passed in `30774193183`.

The first authenticated cache export took 17 minutes 7 seconds. The next warm
prebuild took 1 minute 16 seconds. Consumer jobs showed Buildx steps 8 through
14 as `CACHED`, loaded the 8,192 MB-heap image locally, and never published it.

Manual-tier run
[`30774902565`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30774902565)
passed the 13-test pinned-oracle timezone matrix with `tzdata==2026.3`, a second
13-test API run on the same commit, and all local-only k6 gates. Hosted-runner
availability measured 451.09 ms p95 with 0/1,080 application errors against the
existing 2,300 ms local-Docker threshold. Booking throughput completed 50/50
with zero booking or cleanup errors. Contention produced one success, 19
expected conflicts, one persisted booking, and zero persistence or cleanup
errors.

The same run compared 18 controlled operations with public Cal.diy `main` at
`038381aeca6261635357957d66b8ba85cdb29737`: nine were unchanged, nine changed,
and none was missing. This advisory is not evidence about hosted Cal.com.

That run deliberately ended as cancelled after all manual-only gates completed:
nine concurrent cache consumers starved the duplicate core API import for 19
minutes. The workflow now retains the proven six-consumer push wave and starts
the three manual-only SUT jobs only after the core API job. The cancelled run is
manual-tier evidence for the completed jobs, not a successful overall workflow
conclusion.

`TESTPULSE_DATABASE_URL` and `ENABLE_ALLURE_PAGES` are absent. Accordingly,
TestPulse ingestion was visibly skipped and Pages remains disabled. No
ingestion result, Pages report, green quality conclusion, or CI badge is
claimed. No CI badge is added. The repository remains private.

## Known limitations

The private hosted runner must load a roughly 4.9 GB API image. An authenticated
prewarmed cache removes repeated compilation but still takes roughly three to
five minutes to restore/import under six-way fan-out, before stack bootstrap.
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
