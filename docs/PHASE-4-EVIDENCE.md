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

The final commit-bound availability, booking-throughput, and contention gate
results will be recorded here after the calibrated threshold and validation
contracts are committed. This statement is deliberately pending; the earlier
harness-development runs are not the Phase 4 acceptance record.

## Evidence and reporting

Each run retains its k6 summary, gzip-compressed raw k6 JSON, fixture and
cleanup manifests, plus SUT, host, Docker-resource, k6-version, and
test-repository-commit metadata under the ignored `test-results/performance/`
tree. Threshold outcomes are converted to JUnit with the stable suite name
`caldiy-performance-gates`; detailed latency distributions remain k6
artifacts. TestPulse ingestion remains Phase 5 work and no Phase 4 result has
been sent to it.

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
