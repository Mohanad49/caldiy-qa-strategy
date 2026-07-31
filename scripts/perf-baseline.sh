#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
baseline_root="${repo_root}/test-results/performance/baseline/${timestamp}"
statuses=()

mkdir -p "${baseline_root}"
for run_number in 1 2 3 4 5; do
  printf 'Availability baseline run %s of 5...\n' "${run_number}"
  status=0
  PERF_BASELINE_MODE=1 \
    PERF_RESULT_DIR="${baseline_root}/run-${run_number}" \
    QA_RUN_ID="baseline-${timestamp}-${run_number}" \
    "${repo_root}/scripts/perf-run.sh" availability || status=$?
  statuses+=("${status}")
done

for status in "${statuses[@]}"; do
  if (( status != 0 )); then
    printf 'At least one availability baseline run failed; no threshold was recommended.\n' >&2
    exit 1
  fi
done

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/perf_baseline_analyze.py" \
  --output "${baseline_root}/recommendation.json" \
  "${baseline_root}"/run-*/summary.json
printf 'Baseline evidence: %s\n' "${baseline_root}"
