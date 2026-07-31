#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
result_root="${repo_root}/test-results/performance/contention/${timestamp}"
status=0

mkdir -p "${result_root}"
PERF_RESULT_DIR="${result_root}" QA_RUN_ID="contention-${timestamp}" \
  "${repo_root}/scripts/perf-run.sh" contention || status=$?

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/perf_to_junit.py" \
  --output "${result_root}/junit.xml" \
  "${result_root}/summary.json"

printf 'Contention evidence: %s\n' "${result_root}"
exit "${status}"
