#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
expected="caldiy-qa-strategy"
env_file="${repo_root}/.env"
node_version="$(<"${repo_root}/.nvmrc")"
node_candidate="${NVM_DIR:-${HOME}/.nvm}/versions/node/v${node_version}/bin"

if [[ "${CONFIRM:-}" != "${expected}" ]]; then
  printf 'Snapshot update refused. Re-run with CONFIRM=%s.\n' "${expected}" >&2
  exit 2
fi

if [[ ! -f "${env_file}" ]]; then
  printf 'Missing %s. Run make sut-api-bootstrap first.\n' "${env_file}" >&2
  exit 1
fi
if [[ -x "${node_candidate}/node" ]]; then
  export PATH="${node_candidate}:${PATH}"
fi
if [[ "$(node --version)" != "v${node_version}" ]]; then
  printf 'Node %s is required for visual tests; found %s.\n' "${node_version}" "$(node --version)" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a
export UV_CACHE_DIR="${repo_root}/.cache/uv"
export QA_RUN_ID="${QA_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
export PLAYWRIGHT_JUNIT_OUTPUT="test-results/visual/junit-update.xml"

cd "${repo_root}"
"${repo_root}/scripts/api-smoke.sh"
mkdir -p test-results/visual allure-results/playwright
exec pnpm exec playwright test --project=chromium-visual --update-snapshots
