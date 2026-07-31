#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"
compose=("${repo_root}/scripts/compose.sh")

if [[ ! -f "${env_file}" ]]; then
  printf 'Missing %s. Run make sut-api-bootstrap first.\n' "${env_file}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

"${repo_root}/scripts/smoke.sh" >/dev/null
"${compose[@]}" exec -T redis redis-cli ping | grep -Fxq PONG
curl --fail --silent --show-error "http://localhost:${CALDIY_API_PORT}/health" | grep -Fxq OK
curl --fail --silent --show-error "http://localhost:${CALDIY_API_PORT}/docs-json" | grep -q '"openapi"'

me_response="$(curl --fail --silent --show-error \
  --header "Authorization: Bearer ${CALDIY_API_KEY}" \
  "http://localhost:${CALDIY_API_PORT}/v2/me")"
if [[ "${me_response}" != *'owner1-acme@example.com'* ]]; then
  printf 'Authenticated /v2/me response did not identify the seeded Acme owner.\n' >&2
  exit 1
fi

printf 'API smoke checks passed: complete Phase 1 stack, Redis, health, docs and seeded API-key identity.\n'
