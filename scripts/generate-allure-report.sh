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

stage_dir="$(mktemp -d "${TMPDIR:-/tmp}/caldiy-allure-results.XXXXXX")"
cleanup() {
  rm -rf -- "${stage_dir}"
}
trap cleanup EXIT

# Allure CLI reads one directory but does not recurse into uploaded artifact
# subdirectories. Flatten every raw input into a private staging directory so a
# nested suite (for example api-run-1/) cannot disappear from a "merged" report.
# UUID-based result and attachment names should be unique; reject a conflicting
# basename instead of silently replacing evidence from another suite.
while IFS= read -r -d '' source; do
  destination="${stage_dir}/$(basename "${source}")"
  if [[ -e "${destination}" ]]; then
    if cmp -s -- "${source}" "${destination}"; then
      continue
    fi
    printf 'Conflicting Allure input basename: %s\n' "$(basename "${source}")" >&2
    exit 1
  fi
  cp -- "${source}" "${destination}"
done < <(find "${results_dir}" -type f -print0)

staged_result_count="$(find "${stage_dir}" -maxdepth 1 -type f -name '*-result.json' | wc -l | tr -d ' ')"
[[ "${staged_result_count}" == "${result_count}" ]] || {
  printf 'Allure staging lost results: found %s, staged %s.\n' "${result_count}" "${staged_result_count}" >&2
  exit 1
}

cd "${repo_root}"
pnpm exec allure generate "${stage_dir}" --clean --output "${report_dir}"
[[ -s "${report_dir}/index.html" ]] || {
  printf 'Allure CLI did not generate index.html.\n' >&2
  exit 1
}
generated_case_count="$(find "${report_dir}/data/test-cases" -type f -name '*.json' | wc -l | tr -d ' ')"
[[ "${generated_case_count}" == "${staged_result_count}" ]] || {
  printf 'Allure report lost results: staged %s, generated %s test cases.\n' \
    "${staged_result_count}" "${generated_case_count}" >&2
  exit 1
}
printf 'Generated merged Allure report from %s result files.\n' "${result_count}"
