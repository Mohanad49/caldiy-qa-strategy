#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
result_root="${repo_root}/test-results/performance/gates/${timestamp}"

mkdir -p "${result_root}"
availability_status=0
booking_status=0
PERF_RESULT_DIR="${result_root}/availability" QA_RUN_ID="gates-${timestamp}-availability" \
  "${repo_root}/scripts/perf-run.sh" availability || availability_status=$?
PERF_RESULT_DIR="${result_root}/booking" QA_RUN_ID="gates-${timestamp}-booking" \
  "${repo_root}/scripts/perf-run.sh" booking || booking_status=$?

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/perf_to_junit.py" \
  --output "${result_root}/junit.xml" \
  "${result_root}/availability/summary.json" \
  "${result_root}/booking/summary.json"

printf 'Performance gate evidence: %s\n' "${result_root}"
(( availability_status == 0 && booking_status == 0 ))
