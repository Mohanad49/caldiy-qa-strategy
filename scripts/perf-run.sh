#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scenario="${1:-}"
result_dir="${PERF_RESULT_DIR:-}"
run_id="${QA_RUN_ID:-}"
env_file="${repo_root}/.env"

case "${scenario}" in
  availability) script_name="availability.js" ;;
  booking) script_name="booking-throughput.js" ;;
  contention) script_name="contention.js" ;;
  *)
    printf 'Usage: %s availability|booking|contention\n' "$0" >&2
    exit 2
    ;;
esac

[[ -n "${result_dir}" ]] || {
  printf 'PERF_RESULT_DIR is required.\n' >&2
  exit 2
}
[[ -n "${run_id}" ]] || {
  printf 'QA_RUN_ID is required.\n' >&2
  exit 2
}
[[ -f "${env_file}" ]] || {
  printf 'Missing %s. Run make sut-api-bootstrap first.\n' "${env_file}" >&2
  exit 1
}

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a
export UV_CACHE_DIR="${repo_root}/.cache/uv"

cd "${repo_root}"
"${repo_root}/scripts/api-smoke.sh"
mkdir -p "${result_dir}"

manifest_path="${result_dir}/fixture.json"
summary_path="${result_dir}/summary.json"
raw_path="${result_dir}/raw.json.gz"
metadata_path="${result_dir}/environment.json"
cleanup_path="${result_dir}/cleanup.json"

QA_RUN_ID="${run_id}" PYTEST_XDIST_WORKER="k6" \
  uv run --frozen caldiy-fixtures create --json \
    --time-zone UTC --start-time 00:00 --end-time 23:59 --length-minutes 5 \
  | tee "${manifest_path}" >/dev/null

cleanup_fixture() {
  local cleanup_status=0
  uv run --frozen caldiy-fixtures destroy --json --manifest "${manifest_path}" \
    | tee "${cleanup_path}" >/dev/null || cleanup_status=$?
  return "${cleanup_status}"
}

threshold_ms="60000"
if [[ "${scenario}" == "availability" && "${PERF_BASELINE_MODE:-0}" != "1" ]]; then
  threshold_file="${repo_root}/perf/thresholds.json"
  [[ -f "${threshold_file}" ]] || {
    cleanup_fixture || true
    printf 'Missing measured perf/thresholds.json. Run make perf-baseline first.\n' >&2
    exit 1
  }
  threshold_ms="$(jq -er '.availabilityP95Ms | select(type == "number" and . > 0)' "${threshold_file}")"
fi

uv run --frozen python scripts/perf_metadata.py --output "${metadata_path}"

set +e
"${repo_root}/scripts/k6.sh" run --quiet \
  --summary-export "${summary_path}" \
  --out "json=${raw_path}" \
  --env "CALDIY_API_URL=http://localhost:${CALDIY_API_PORT}" \
  --env "CALDIY_API_KEY=${CALDIY_API_KEY}" \
  --env "PERF_FIXTURE_MANIFEST=${manifest_path}" \
  --env "PERF_AVAILABILITY_P95_MS=${threshold_ms}" \
  --env "PERF_BASELINE_MODE=${PERF_BASELINE_MODE:-0}" \
  --env "QA_RUN_ID=${run_id}" \
  "${repo_root}/perf/k6/${script_name}"
k6_status=$?
set -e

cleanup_status=0
cleanup_fixture || cleanup_status=$?
if (( cleanup_status != 0 )); then
  printf 'Performance fixture cleanup failed; see %s.\n' "${cleanup_path}" >&2
fi
if (( k6_status != 0 )); then
  printf 'k6 %s scenario failed; summary: %s\n' "${scenario}" "${summary_path}" >&2
fi
(( k6_status == 0 && cleanup_status == 0 ))
