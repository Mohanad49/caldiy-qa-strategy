#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cache_dir="${repo_root}/.cache/cal-diy-main-advisory"
source_url="https://github.com/calcom/cal.diy.git"
result_dir="${repo_root}/test-results/contracts/current-upstream"

mkdir -p "${cache_dir}" "${result_dir}"
if [[ ! -d "${cache_dir}/.git" ]]; then
  git -C "${cache_dir}" init
  git -C "${cache_dir}" remote add origin "${source_url}"
fi
[[ "$(git -C "${cache_dir}" remote get-url origin)" == "${source_url}" ]] || {
  printf 'Unexpected advisory source remote.\n' >&2
  exit 1
}
[[ -z "$(git -C "${cache_dir}" status --short)" ]] || {
  printf 'Current-upstream advisory cache is dirty.\n' >&2
  exit 1
}

git -C "${cache_dir}" fetch --depth 1 origin main
git -C "${cache_dir}" checkout --detach FETCH_HEAD
current_sha="$(git -C "${cache_dir}" rev-parse HEAD)"
current_spec="${cache_dir}/docs/api-reference/v2/openapi.json"

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/current_upstream_contract_advisory.py" \
  --current-spec "${current_spec}" \
  --current-sha "${current_sha}" \
  --json-output "${result_dir}/advisory.json" \
  --markdown-output "${result_dir}/summary.md"
cat "${result_dir}/summary.md"
