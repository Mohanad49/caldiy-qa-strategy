#!/usr/bin/env bash
set -euo pipefail

android_root="/usr/local/lib/android"

[[ "${CI:-}" == "true" ]] || {
  printf 'ci-free-disk.sh is restricted to CI.\n' >&2
  exit 1
}
[[ "${RUNNER_ENVIRONMENT:-}" == "github-hosted" && "${RUNNER_OS:-}" == "Linux" ]] || {
  printf 'Disk cleanup is restricted to ephemeral GitHub-hosted Linux runners.\n' >&2
  exit 1
}

printf 'Runner disk before removing the unused Android SDK:\n'
df -h /

if [[ -d "${android_root}" ]]; then
  sudo rm -rf -- "${android_root}"
else
  printf 'Unused Android SDK was already absent at %s.\n' "${android_root}"
fi

[[ ! -e "${android_root}" ]] || {
  printf 'Failed to remove the unused Android SDK at %s.\n' "${android_root}" >&2
  exit 1
}

printf 'Runner disk after removing the unused Android SDK:\n'
df -h /
