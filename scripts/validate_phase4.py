#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Phase 4 validation failed: {message}")


def main() -> None:
    required_files = (
        "docs/PHASE-4-EVIDENCE.md",
        "perf/fixture.example.json",
        "perf/thresholds.json",
        "perf/k6/common.js",
        "perf/k6/availability.js",
        "perf/k6/booking-throughput.js",
        "perf/k6/contention.js",
        "scripts/k6.sh",
        "scripts/perf-baseline.sh",
        "scripts/perf-test.sh",
        "scripts/perf-contention.sh",
        "scripts/perf-run.sh",
        "scripts/perf_baseline_analyze.py",
        "scripts/perf_metadata.py",
        "scripts/perf_to_junit.py",
        "scripts/wait-api-budget.sh",
    )
    for relative_path in required_files:
        path = ROOT / relative_path
        require(path.is_file() and path.stat().st_size > 0, f"missing or empty {relative_path}")

    thresholds = json.loads(read("perf/thresholds.json"))
    require(thresholds.get("schemaVersion") == 1, "threshold schema version changed")
    run_values = thresholds.get("basis", {}).get("runP95Ms")
    require(
        isinstance(run_values, list)
        and len(run_values) == 5
        and all(isinstance(value, (int, float)) and value > 0 for value in run_values),
        "availability threshold must be based on five positive run-level p95 values",
    )
    worst = max(run_values)
    expected_gate = int(math.ceil(max(500.0, worst * 1.25) / 50.0) * 50)
    require(
        math.isclose(float(thresholds["basis"]["worstRunP95Ms"]), worst),
        "recorded worst-run p95 does not match the five-run baseline",
    )
    require(
        thresholds.get("availabilityP95Ms") == expected_gate,
        "availability gate does not implement the declared calibration policy",
    )
    scope = str(thresholds.get("scope", "")).lower()
    require("local amd64 docker" in scope, "threshold scope must identify local amd64 Docker")
    require("not a production slo" in scope, "threshold must explicitly reject production-SLO status")

    k6_wrapper = read("scripts/k6.sh")
    require('k6_version="2.1.0"' in k6_wrapper, "k6 version pin changed")
    for checksum in (
        "a600f44ad411ad5f5f7d178405d9956dac34c43563341396f1017ae7f79221a9",
        "295d961ebfca306f295f1133068dcd403a8171c87f387928f5f30b0fbcff858a",
    ):
        require(checksum in k6_wrapper, f"missing pinned k6 archive checksum {checksum}")

    availability = read("perf/k6/availability.js")
    for contract in (
        'vus: 20',
        'duration: "60s"',
        'duration: "10s"',
        'sleep(1)',
        'slotsUrl(8)',
        'availability_errors: ["rate<0.01"]',
        'publicHeaders("2024-09-04"',
    ):
        require(contract in availability, f"availability contract missing: {contract}")

    booking = read("perf/k6/booking-throughput.js")
    for contract in (
        'vus: 10',
        'iterations: 50',
        'slots.length < 50',
        'slots.slice(0, 50)',
        'iterationInTest',
        'cancelBooking(booking.uid)',
        'booking_errors: ["rate<0.01"]',
        'booking_cleanup_errors: ["count==0"]',
    ):
        require(contract in booking, f"booking-throughput contract missing: {contract}")

    contention = read("perf/k6/contention.js")
    for contract in (
        'executor: "per-vu-iterations"',
        'vus: 20',
        'iterations: 1',
        'contention_successes: ["count==1"]',
        'contention_conflicts: ["count==19"]',
        'contention_persisted_bookings: ["value==1"]',
        'contention_unexpected_responses: ["count==0"]',
        'contention_persistence_errors: ["count==0"]',
        'contention_cleanup_errors: ["count==0"]',
    ):
        require(contract in contention, f"contention contract missing: {contract}")

    all_k6 = "\n".join(read(path) for path in (
        "perf/k6/common.js",
        "perf/k6/availability.js",
        "perf/k6/booking-throughput.js",
        "perf/k6/contention.js",
    ))
    urls = re.findall(r'https?://[^"\'`\s]+', all_k6)
    require(
        all(url.startswith("http://localhost:") for url in urls),
        f"performance scripts contain a non-local target: {urls}",
    )

    wrappers = "\n".join(read(path) for path in (
        "scripts/perf-run.sh",
        "scripts/perf-baseline.sh",
        "scripts/perf-test.sh",
        "scripts/perf-contention.sh",
        "scripts/wait-api-budget.sh",
    ))
    for forbidden in ("psql", "redis-cli", "flushall", "flushdb"):
        require(forbidden not in wrappers.lower(), f"performance harness bypasses state through {forbidden}")
    require(
        '--env "CALDIY_API_URL=http://localhost:${CALDIY_API_PORT}"' in wrappers,
        "performance wrapper does not force the SUT to loopback",
    )

    makefile = read("Makefile")
    for target in ("perf-baseline:", "test-perf:", "test-contention:"):
        require(target in makefile, f"stable Make target missing: {target}")

    junit = read("scripts/perf_to_junit.py")
    require(
        'name="caldiy-performance-gates"' in junit,
        "JUnit suite name must remain stable for future TestPulse ingestion",
    )
    require(
        'values = {key: value for key, value in metric.items() if key != "thresholds"}' in junit,
        "JUnit cases must retain the measured k6 values",
    )

    metadata = read("scripts/perf_metadata.py")
    require(
        "1c193cca8682b33b9866c792186033f7ef886682" in metadata,
        "performance metadata lost the controlled Cal.diy source commit",
    )
    for field in ("testRepositoryCommit", "memoryBytes", "containers", "k6Version"):
        require(field in metadata, f"performance metadata field missing: {field}")

    evidence = read("docs/PHASE-4-EVIDENCE.md")
    for heading in (
        "## Product boundary",
        "## Workloads and isolation",
        "## Five-run local baseline",
        "## Acceptance results",
        "## Evidence and reporting",
        "## Limitations",
    ):
        require(heading in evidence, f"Phase 4 evidence heading missing: {heading}")
    evidence_lower = " ".join(evidence.lower().split())
    require("not a production slo" in evidence_lower, "evidence must reject a production-SLO claim")
    require("testpulse" in evidence_lower and "phase 5" in evidence_lower, "TestPulse deferral is missing")

    print("Phase 4 static contracts passed.")


if __name__ == "__main__":
    main()
