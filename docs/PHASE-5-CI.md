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

Every job uses the explicit stable `ubuntu-24.04` runner label. The moving
`ubuntu-latest` alias is forbidden by repository validation so an operating
system transition cannot silently redefine the visual or runtime environment.

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

The repository-owned composite adapter installs `testpulse-core[postgres]`
from exact TestPulse commit
`2696d715e7b18f2ef029e291f37371d6b4bb01fb` and pins its Python setup action by
full SHA. The setup action is `v7.0.0`, whose action metadata uses Node 24; this
replaces the passing-but-deprecated Node 20 runtime observed during the final
audit. The adapter exists because the upstream action at that commit installs its
package from mutable `main`; pinning only the outer action did not make the
executed package immutable.

The adapter receives `TESTPULSE_DATABASE_URL` only as a masked secret input.
Secret checks emit only a boolean presence output. Ingestion is
`continue-on-error`: a TestPulse outage cannot change product confidence, while
the adapter adds an error annotation and workflow-summary failure record.

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
confirmed `TESTPULSE_DATABASE_URL` by boolean presence only, but it did **not**
prove all five ingestion calls. The once-merged E2E input succeeded as TestPulse
run 163. Core API, repeated API, BDD, and performance each failed before ingest:
hosted `pipx` required `uv >= 0.9.17`, while those jobs had installed `uv 0.8.17`.
Because reporting is deliberately non-blocking, the product gates kept their own
conclusions and the TestPulse action left error annotations and summaries. The
earlier documentation incorrectly treated the continued steps as successful;
this paragraph is the corrected audit record.

Push audit run
[`30960025297`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30960025297)
raised the pinned CI `uv` version to `0.12.1`. Its live API suite passed 13/13,
all four Playwright shards merged to 15/15, and BDD passed 3/3. The corresponding
TestPulse ingestions succeeded as runs 165 (`caldiy-api-v2`), 166
(`caldiy-bdd`), and 167 (`caldiy-e2e`). The same run retained the expected axe
failure and generated the inspected hosted-Linux visual actuals used to create
platform-specific baselines. No database URL was printed or copied.

Run
[`30961268898`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30961268898)
then proved the repository-owned, exact-commit TestPulse adapter: API, merged
E2E and BDD were stored as runs 168, 169 and 170. Desktop visual comparison
passed; mobile differed by 24 dynamic-date pixels, which exposed that masking
individual calendar children was not stable across changing child counts.

Run
[`30962249720`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30962249720)
proved the fixed-section approach was still too broad on mobile: its retained
actual was a full-page magenta mask. That artifact was explicitly rejected and
never imported. The failure led to runtime guards that reject metadata coverage
or at least 75% viewport coverage, plus a mobile selector for the inner calendar
box only. This is a test-harness correction, not a product finding.

On explicit `ubuntu-24.04`, run
[`30963385880`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30963385880)
passed the desktop comparison and produced one meaningful mobile actual: event
metadata, timezone, time-format controls and slot buttons remained compared;
only the dynamic calendar rectangle was masked. That inspected mobile image was
imported with the guarded partial importer while the already-passing desktop
baseline was preserved. API, merged E2E and BDD again passed and entered
TestPulse as runs 174, 175 and 176. An ordinary hosted comparison after that
import is the acceptance boundary, not the import itself.

Ordinary push run
[`30964383774`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30964383774)
closed that boundary on commit
`01c6ab30cfb0a95daee258dfb007c9346095f033`. Its retained visual JUnit contains
two tests with zero failures: both 1440×900 and 390×844 passed without update
mode. BDD passed 3/3, the API suite passed 13/13, all four Playwright shards and
the once-merged 15-test report passed, and the merged Allure artifact succeeded.
The browser-quality job failed only when its final enforcement step propagated
the unchanged one-pass/two-fail axe report.

That run also surfaced a hosted-runner deprecation annotation for the
TestPulse adapter's old Node 20 `setup-python` action. The repository repinned
the adapter to official `setup-python` `v7.0.0` commit
`5fda3b95a4ea91299a34e894583c3862153e4b97`, whose action metadata declares
Node 24, and repository validation now enforces that exact revision.

Push run
[`30965349762`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30965349762)
then proved that replacement on commit
`97eee19bcca18b1c6fc58efa72428ce19a6ec6d8`. API, BDD and once-merged E2E
ingestion all succeeded through the repository-owned adapter, with no Node 20
deprecation annotation. The API suite, four shards, merge, visuals and Allure
again passed; final workflow failure remained isolated to the unchanged axe
report and its enforcement step.

Final manual/nightly-equivalent release run
[`30966169388`](https://github.com/Mohanad49/caldiy-qa-strategy/actions/runs/30966169388)
then exercised that exact commit through every hosted tier on explicit
`ubuntu-24.04`. Core and repeated API reports each contain 13 tests with zero
failures, the once-merged E2E report contains 15 tests with zero failures, BDD
contains three tests with zero failures, the pinned-oracle timezone report
contains 14 tests with zero failures, and the visual report contains two tests
with zero failures. Accessibility contains three tests and two failures. All
four shards, the complete contract check, current-main advisory, k6 gates and
merged Allure report succeeded.

The hosted availability gate observed 0/1,043 application errors and 427.503 ms
p95 across its measured calls, under the existing 2,300 ms local-Docker gate;
1,062 HTTP calls include warm-up and setup traffic. Booking throughput completed
50/50 with zero application or cleanup errors and an informational 2,090.065 ms
request p95. Contention produced one success, 19 expected conflicts and one
persisted booking, with zero unexpected, persistence or cleanup errors. The
merged performance JUnit contains ten tests with zero failures.

The same run stored BDD as TestPulse run 183, core API as 184, merged E2E as
185, repeated API as 186, and performance gates as 187. The current-public-main
advisory still observed exact commit
`8418db70c71e5364e6baf26275aafa10e6bc9bd7`: nine controlled operations were
unchanged, nine changed and none was missing; both filed defect conditions were
still reproduced. The workflow's only failing job was browser quality, whose
final enforcement propagated the unchanged one-pass/two-fail axe result after
BDD, visuals, evidence upload and TestPulse ingestion succeeded. All other 13
jobs passed. Check runs carried only the two expected browser failure
annotations and no action-runtime deprecation annotation.

The raw logs do retain two upstream maintenance notices: the historical
Cal.diy seed uses the Prisma `package.json#prisma` configuration deprecated for
Prisma 7, and official `actions/download-artifact` `v8.0.1` emits Node's legacy
`Buffer()` warning. Neither is hidden or treated as a product failure; both are
covered by the monthly pin review, while changing the historical SUT solely to
silence its warning remains out of scope.

Database ingestion and public static export are separate boundaries. At this
checkpoint the public TestPulse export was generated on 2026-08-04 and did not
yet contain the private Cal.diy repository's run summaries. Publishing those
summaries requires explicit owner approval or a refresh after this repository
becomes public; successful ingestion is not misreported as an already-refreshed
dashboard.

Mohanad explicitly approved publication on 2026-08-09. TestPulse CI run
[`31284812109`](https://github.com/Mohanad49/testpulse/actions/runs/31284812109)
passed backend, frontend, E2E/accessibility, Docker, migration, export, and
deployment jobs. Its public index was generated at
`2026-08-08T23:52:07.407444+00:00` and contains all four Cal.diy suite names.
The public API, BDD, and E2E summaries include Cal.diy commit
`1907d5997f1b252f0230d1e0ecb392c6cbdc65db` at 13/13, 3/3, and 15/15; the
performance summary remains the latest scheduled 10/10 gate run because a push
does not execute load tests. All four summaries report zero current failures,
zero flaky or newly failing tests, and zero quarantine debt. A post-deployment
scan found no database URL, token, private-key marker, local path, runner path,
or seeded API-key pattern in the published JSON.

No CI badge is shown: the complete workflow remains red for the enforced,
unsuppressed accessibility findings even when infrastructure, functional,
reporting and visual checks pass.

Eligible inputs use the four declared suite names. Core and repeated API runs
intentionally share `caldiy-api-v2` to create same-commit history rather than a
fifth suite.

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
amd64 Docker workstation. Manual hosted-runner results are retained as separate
environment evidence; they neither recalibrate that workstation gate nor make
it representative of all GitHub runners. It remains explicitly not a production
SLO.

The historical snapshot has evidence-backed serious/critical accessibility
findings. The CI accessibility gate keeps those failures red; Phase 5 does not
suppress them to obtain a green workflow or badge.
