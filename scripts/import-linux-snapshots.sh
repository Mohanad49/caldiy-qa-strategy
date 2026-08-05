#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
expected="caldiy-qa-strategy"
source_root="${SOURCE_DIR:-}"
destination="${repo_root}/__screenshots__/linux/tests/visual/booking.visual.spec.ts"

if [[ "${CONFIRM:-}" != "${expected}" ]]; then
  printf 'Linux snapshot import refused. Re-run with CONFIRM=%s.\n' "${expected}" >&2
  exit 2
fi
if [[ -z "${source_root}" || ! -d "${source_root}" ]]; then
  printf 'SOURCE_DIR must be the extracted browser failure artifact.\n' >&2
  exit 2
fi

mkdir -p "${destination}"
imported_count=0
for viewport in 1440x900 390x844; do
  source_file=""
  match_count=0
  while IFS= read -r candidate; do
    source_file="${candidate}"
    match_count=$((match_count + 1))
  done < <(find "${source_root}" -type f -name "public-booking-${viewport}-actual.png" -print)

  if [[ "${match_count}" -eq 0 ]]; then
    printf 'No failed %s actual in this artifact; preserving its passing Linux baseline.\n' "${viewport}"
    continue
  fi
  if [[ "${match_count}" -ne 1 ]]; then
    printf 'Expected one %s Linux actual; found %s.\n' "${viewport}" "${match_count}" >&2
    exit 1
  fi
  file "${source_file}" | grep -Fq "PNG image data, ${viewport/x/ x }" || {
    printf 'Unexpected PNG dimensions for %s: %s\n' "${viewport}" "${source_file}" >&2
    exit 1
  }
  cp "${source_file}" "${destination}/public-booking-${viewport}.png"
  imported_count=$((imported_count + 1))
  printf 'Imported inspected Linux baseline: %s\n' "${viewport}"
done

if [[ "${imported_count}" -eq 0 ]]; then
  printf 'No failed visual actuals were available to import.\n' >&2
  exit 1
fi

UV_CACHE_DIR="${repo_root}/.cache/uv" uv run --frozen python \
  "${repo_root}/scripts/validate_phase3.py"
