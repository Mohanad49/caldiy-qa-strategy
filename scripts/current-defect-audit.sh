#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cache_dir="${repo_root}/.cache/cal-diy-main-advisory"
result_dir="${repo_root}/test-results/defects/current-main"

"${repo_root}/scripts/current-upstream-advisory.sh" >/dev/null
current_sha="$(git -C "${cache_dir}" rev-parse HEAD)"

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/current_defect_audit.py" \
  --source-root "${cache_dir}" \
  --current-sha "${current_sha}" \
  --json-output "${result_dir}/audit.json" \
  --markdown-output "${result_dir}/summary.md"

cat "${result_dir}/summary.md"
