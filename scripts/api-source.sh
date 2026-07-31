#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${repo_root}/.cache/cal-diy-v6.2.0"
source_url="https://github.com/calcom/cal.diy.git"
source_sha="1c193cca8682b33b9866c792186033f7ef886682"

command -v git >/dev/null 2>&1 || {
  printf 'Required command is missing: git\n' >&2
  exit 1
}

if [[ ! -d "${source_dir}/.git" ]]; then
  mkdir -p "${source_dir}"
  git -C "${source_dir}" init
  git -C "${source_dir}" remote add origin "${source_url}"
  git -C "${source_dir}" fetch --depth 1 origin "${source_sha}"
  git -C "${source_dir}" checkout --detach FETCH_HEAD
fi

actual_origin="$(git -C "${source_dir}" remote get-url origin)"
if [[ "${actual_origin}" != "${source_url}" ]]; then
  printf 'Unexpected Cal.diy source remote: %s\n' "${actual_origin}" >&2
  exit 1
fi

actual_sha="$(git -C "${source_dir}" rev-parse HEAD)"
if [[ "${actual_sha}" != "${source_sha}" ]]; then
  printf 'Cal.diy source HEAD is %s; expected %s.\n' "${actual_sha}" "${source_sha}" >&2
  printf 'The cache is never reset automatically. Remove it deliberately and rerun.\n' >&2
  exit 1
fi

if [[ -n "$(git -C "${source_dir}" status --short)" ]]; then
  printf 'Cal.diy source cache has local changes; refusing a non-reproducible build.\n' >&2
  exit 1
fi

printf '%s\n' "${source_dir}"
