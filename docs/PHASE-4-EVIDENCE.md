# Phase 4 — Local performance and contention evidence

## Product boundary

These checks exercise the controlled `calcom/cal.diy` `v6.2.0` snapshot at
commit `1c193cca8682b33b9866c792186033f7ef886682`. They run only against the
loopback API v2 service in this repository's private, project-scoped Docker
environment. They do not measure current Cal.diy, hosted Cal.com, or public
infrastructure.

## Workloads and isolation

Availability uses two virtual users for a ten-second warm-up, then 20 virtual
users for 60 seconds. Each virtual user pauses one second between calls and has
its own `x-cal-client-id`. Calls use the public slots interface, an eight-day
UTC range, and an isolated 30-minute event type created through the Phase 2
fixture CLI.

Booking throughput uses ten virtual users for 50 total iterations. Every
iteration has a unique slot and attendee identity, then cancels its booking
through the supported API. Fifty iterations are intentional: the official
seed API key is limited to 120 requests per minute, and the harness waits for
the real budget rather than changing application state or rate-limit policy.

Contention synchronizes 20 one-iteration virtual users on one capacity-one
slot. Its acceptance invariant is exactly one HTTP 201, exactly 19 expected
HTTP 400/409 conflict responses, and exactly one booking returned by the
supported booking-list API for that event and instant. The winner is cancelled
through the supported endpoint.

## Five-run local baseline

The clean baseline recorded availability p95 values of 894.964, 1,811.045,
705.000, 1,003.723, and 535.255 ms, with a 0% application error rate in every
run. The policy is the larger of 500 ms or 125% of the worst run-level p95,
rounded up to 50 ms. The resulting gate is **2,300 ms**.

This is a local amd64 Docker threshold for this controlled environment, not a
production SLO. The baseline metadata identifies test-repository commit
`465d1bf`, Darwin x86_64, Docker Server 20.10.22 with 8,240,787,456 bytes
available to Docker, and k6 v2.1.0.

## Acceptance results

The final acceptance runs used test-repository commit
`50224cada92517ae10198a9ec7472e7eec1709bc`, which contains the exact harness,
calibrated threshold, and Phase 4 static contracts.

- Availability passed with p95 **1,408.838 ms** against the 2,300 ms gate and
  zero application errors across 924 measured calls. Its raw HTTP set contained
  942 calls including warm-up traffic, also with zero failures.
- Booking throughput completed **50 of 50** unique-slot bookings with zero
  application errors and zero cleanup errors. The booking request p95 was
  2,725.477 ms; it is retained as a measurement, not presented as a calibrated
  gate or production target. All 101 HTTP calls, including slot discovery and
  supported cancellations, succeeded.
- Contention produced exactly **1 success, 19 expected conflicts, and 1
  persisted booking**, with zero unexpected responses, persistence errors, or
  cleanup errors. Contention request p95 was 3,543.231 ms and is informational.
  k6 reports a generic HTTP failure rate of 82.61% because the 19 expected
  HTTP 400/409 conflict responses are non-success statuses; the contention
  integrity metrics classify and gate those responses separately.

The availability and booking run produced four passing JUnit threshold cases.
The contention run produced six passing JUnit threshold cases. Both JUnit files
use the stable `caldiy-performance-gates` suite name and contain zero failures.

## Final local recheck

The 2026-08-05 release audit reran both stable commands against the cleanly
rebuilt stack. Availability completed 871 measured iterations with zero
application errors and p95 1,212.828 ms under the 2,300 ms gate; the raw HTTP
set contained 889 calls including warm-up. Booking throughput completed 50 of
50 unique bookings with zero application or cleanup errors and an informational
2,756.148 ms request p95. Contention again produced exactly one success, 19
expected conflicts and one persisted booking, with zero unexpected,
persistence or cleanup errors.

## Evidence and reporting

Each run retains its k6 summary, gzip-compressed raw k6 JSON, fixture and
cleanup manifests, plus SUT, host, Docker-resource, k6-version, and
test-repository-commit metadata under the ignored `test-results/performance/`
tree. Threshold outcomes are converted to JUnit with the stable suite name
`caldiy-performance-gates`; detailed latency distributions remain k6
artifacts. Phase 5 owns eligible TestPulse ingestion and records its actual CI
evidence separately.

k6 is pinned to v2.1.0. The project verifies upstream release archives before
extraction with SHA-256
`a600f44ad411ad5f5f7d178405d9956dac34c43563341396f1017ae7f79221a9`
for macOS amd64 and
`295d961ebfca306f295f1133068dcd403a8171c87f387928f5f30b0fbcff858a`
for Linux amd64.

## Limitations

The measurements are workstation-specific and cannot establish production
capacity, latency, or an SLO. Authenticated workloads are deliberately bounded
by the official fixture API key's 120-request-per-minute policy. Expected
contention conflicts are HTTP failures from k6's generic perspective, so they
are counted separately from unexpected transport or application errors.
Historical booking rows remain after supported cancellation until the guarded,
project-scoped checkpoint reset removes the local volumes.
