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
  printf 'uv is required. Run make test-bootstrap after installing uv.\n' >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a
export QA_RUN_ID="${QA_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"

"${repo_root}/scripts/api-smoke.sh"
mkdir -p test-results/api allure-results/api
find test-results/api -maxdepth 1 -type f -name 'contract-omissions-*.json' -delete
uv run --frozen pytest tests/api \
  -n 4 \
  --dist loadscope \
  --junitxml=test-results/api/junit.xml \
  --alluredir=allure-results/api \
  --clean-alluredir \
  --cov=caldiy_qa \
  --cov-report=term-missing \
  --cov-report=xml:test-results/api/coverage.xml
