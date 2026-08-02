#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose=("${repo_root}/scripts/compose.sh")
image_name="caldiy-api-v2:6.2.0-local"

[[ "${CI:-}" == "true" ]] || {
  printf 'ci-sut-bootstrap.sh is restricted to CI.\n' >&2
  exit 1
}
docker image inspect "${image_name}" >/dev/null 2>&1 || {
  printf 'Missing runner-local %s.\n' "${image_name}" >&2
  exit 1
}

"${repo_root}/scripts/bootstrap.sh"
"${repo_root}/scripts/api-license.sh"
"${compose[@]}" --profile api up -d redis api-v2

wait_for_health() {
  local service="$1"
  local timeout_seconds="$2"
  local started_at container_id status
  started_at="$(date +%s)"
  while true; do
    container_id="$(${compose[@]} --profile api ps -q "${service}")"
    status=""
    if [[ -n "${container_id}" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")"
    fi
    [[ "${status}" == "healthy" ]] && return 0
    if [[ "${status}" == "unhealthy" || "${status}" == "exited" || "${status}" == "dead" ]]; then
      "${compose[@]}" --profile api logs --tail 150 "${service}" >&2
      printf 'Service %s entered %s.\n' "${service}" "${status}" >&2
      return 1
    fi
    if (( $(date +%s) - started_at >= timeout_seconds )); then
      "${compose[@]}" --profile api logs --tail 150 "${service}" >&2
      printf 'Timed out waiting for %s.\n' "${service}" >&2
      return 1
    fi
    sleep 3
  done
}

wait_for_health redis 180
wait_for_health api-v2 600
"${repo_root}/scripts/api-smoke.sh"
printf 'CI SUT bootstrap passed without repeating the ten-minute local qualification.\n'
