#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"
compose=("${repo_root}/scripts/compose.sh")

if [[ ! -f "${env_file}" ]]; then
  printf 'Missing %s. Run make sut-bootstrap first.\n' "${env_file}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

"${compose[@]}" exec -T postgres pg_isready -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" >/dev/null
curl --fail --silent --show-error --location "http://localhost:${CALDIY_WEB_PORT}/" >/dev/null
curl --fail --silent --show-error --location "http://localhost:${CALDIY_WEB_PORT}/pro/30min" >/dev/null
curl --fail --silent --show-error "http://localhost:${MAILPIT_HTTP_PORT}/" >/dev/null

printf 'Smoke checks passed: PostgreSQL, Cal.diy home, seeded booking page, Mailpit.\n'
