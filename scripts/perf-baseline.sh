#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
baseline_root="${repo_root}/test-results/performance/baseline/${timestamp}"

mkdir -p "${baseline_root}"
for run_number in 1 2 3 4 5; do
  printf 'Availability baseline run %s of 5...\n' "${run_number}"
  if ! PERF_BASELINE_MODE=1 \
    PERF_RESULT_DIR="${baseline_root}/run-${run_number}" \
    QA_RUN_ID="baseline-${timestamp}-${run_number}" \
    "${repo_root}/scripts/perf-run.sh" availability; then
    printf 'Availability baseline run %s failed; no later runs or threshold were produced.\n' \
      "${run_number}" >&2
    exit 1
  fi
done

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/perf_baseline_analyze.py" \
  --output "${baseline_root}/recommendation.json" \
  "${baseline_root}"/run-*/summary.json
printf 'Baseline evidence: %s\n' "${baseline_root}"
