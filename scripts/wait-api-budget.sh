#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
required_remaining="${1:-}"
env_file="${repo_root}/.env"
headers_dir="${repo_root}/.cache/perf-budget"
headers_file="${headers_dir}/headers.txt"

[[ "${required_remaining}" =~ ^[0-9]+$ ]] || {
  printf 'Usage: %s REQUIRED_REMAINING_REQUESTS\n' "$0" >&2
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
mkdir -p "${headers_dir}"

for attempt in 1 2 3; do
  status="$(curl --silent --show-error \
    --dump-header "${headers_file}" \
    --output /dev/null \
    --write-out '%{http_code}' \
    --header "Authorization: Bearer ${CALDIY_API_KEY}" \
    "http://localhost:${CALDIY_API_PORT}/v2/me")"
  remaining="$(awk 'tolower($1) == "x-ratelimit-remaining-default:" \
    { gsub("\\r", "", $2); value=$2 } END { print value }' \
    "${headers_file}")"
  reset_ms="$(awk 'tolower($1) == "x-ratelimit-reset-default:" \
    { gsub("\\r", "", $2); value=$2 } END { print value }' \
    "${headers_file}")"

  if [[ "${status}" == "200" && "${remaining}" =~ ^[0-9]+$ ]] && \
    (( remaining >= required_remaining )); then
    printf 'API-key budget ready: %s requests remain; %s required.\n' \
      "${remaining}" "${required_remaining}"
    exit 0
  fi
  [[ "${reset_ms}" =~ ^[0-9]+$ ]] || {
    printf 'API budget response lacked usable rate-limit headers (HTTP %s).\n' "${status}" >&2
    exit 1
  }
  if (( reset_ms <= 120 )); then
    wait_seconds=$((reset_ms + 1))
  else
    wait_seconds=$(( (reset_ms + 999) / 1000 + 1 ))
  fi
  if (( wait_seconds > 65 )); then
    wait_seconds=65
  fi
  printf 'API-key budget is %s/%s (HTTP %s); waiting %s seconds for reset.\n' \
    "${remaining:-unknown}" "${required_remaining}" "${status}" "${wait_seconds}"
  sleep "${wait_seconds}"
done

printf 'API-key budget did not recover after three checks.\n' >&2
exit 1
