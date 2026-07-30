#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"

if [[ ! -f "${env_file}" ]]; then
  printf 'Missing %s. Run make sut-bootstrap first.\n' "${env_file}" >&2
  exit 1
fi

exec docker compose \
  --project-name caldiy-qa-strategy \
  --env-file "${env_file}" \
  --file "${repo_root}/infra/compose.yml" \
  "$@"
