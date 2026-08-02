#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
results_dir="${1:-${repo_root}/allure-results}"
report_dir="${2:-${repo_root}/allure-report}"

[[ -d "${results_dir}" ]] || {
  printf 'Allure results directory does not exist: %s\n' "${results_dir}" >&2
  exit 1
}
result_count="$(find "${results_dir}" -type f -name '*-result.json' | wc -l | tr -d ' ')"
(( result_count > 0 )) || {
  printf 'No Allure test result files were found in %s.\n' "${results_dir}" >&2
  exit 1
}

cd "${repo_root}"
pnpm exec allure generate "${results_dir}" --clean --output "${report_dir}"
[[ -s "${report_dir}/index.html" ]] || {
  printf 'Allure CLI did not generate index.html.\n' >&2
  exit 1
}
printf 'Generated merged Allure report from %s result files.\n' "${result_count}"
