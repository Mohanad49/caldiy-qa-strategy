#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"
cd "${repo_root}"
export UV_CACHE_DIR="${repo_root}/.cache/uv"

if [[ ! -f "${env_file}" ]]; then
  printf 'Missing %s. Run make sut-api-bootstrap first.\n' "${env_file}" >&2
  exit 1
fi
if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Run make test-bootstrap first.\n' >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

"${repo_root}/scripts/api-smoke.sh" >/dev/null
uv run --frozen python -m caldiy_qa.contracts \
  --runtime-url "http://localhost:${CALDIY_API_PORT}"
