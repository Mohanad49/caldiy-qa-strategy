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
Cal.com.

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

The workflow has not yet run from the Phase 5 implementation commit. No CI
suite result, TestPulse ingestion, merged Allure artifact, or quality-workflow
conclusion is claimed here until GitHub produces it. The existing repository
remains private, and no CI badge is added at this checkpoint.

## Known limitations

The private hosted runner must rebuild and load a roughly 4.9 GB API image. A
prewarmed cache reduces compilation but does not remove runner memory and disk
pressure. Failure at either the upstream 8,192 MB heap or the documented 6,144
MB OOM fallback remains a real CI infrastructure failure; the workflow does not
substitute API v1 or hosted Cal.com.

The Phase 4 2,300 ms availability threshold was calibrated on the controlled
amd64 Docker workstation. Nightly CI applies it as the existing local-Docker
gate, but the first hosted-runner evidence must be reviewed before describing
it as representative of that runner class. It remains explicitly not a
production SLO.

The historical snapshot has evidence-backed serious/critical accessibility
findings. The CI accessibility gate keeps those failures red; Phase 5 does not
suppress them to obtain a green workflow or badge.
