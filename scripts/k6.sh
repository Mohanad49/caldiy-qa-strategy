#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
k6_version="2.1.0"
system_name="$(uname -s)"
machine_arch="$(uname -m)"

case "${system_name}:${machine_arch}" in
  Darwin:x86_64)
    archive="k6-v${k6_version}-macos-amd64.zip"
    checksum="a600f44ad411ad5f5f7d178405d9956dac34c43563341396f1017ae7f79221a9"
    ;;
  Linux:x86_64 | Linux:amd64)
    archive="k6-v${k6_version}-linux-amd64.tar.gz"
    checksum="295d961ebfca306f295f1133068dcd403a8171c87f387928f5f30b0fbcff858a"
    ;;
  *)
    printf 'k6 %s is pinned only for Darwin/Linux amd64; found %s/%s.\n' \
      "${k6_version}" "${system_name}" "${machine_arch}" >&2
    exit 1
    ;;
esac

tool_root="${repo_root}/.cache/tools/k6-v${k6_version}-${system_name}-${machine_arch}"
archive_path="${tool_root}/${archive}"
binary_path="${tool_root}/k6"

verify_checksum() {
  local actual
  actual="$(shasum -a 256 "$1" | awk '{print $1}')"
  [[ "${actual}" == "${checksum}" ]] || {
    printf 'k6 archive checksum mismatch: expected %s, got %s.\n' "${checksum}" "${actual}" >&2
    return 1
  }
}

if [[ ! -x "${binary_path}" ]]; then
  mkdir -p "${tool_root}"
  if [[ ! -f "${archive_path}" ]] || ! verify_checksum "${archive_path}"; then
    printf 'Downloading pinned k6 v%s for %s/%s...\n' \
      "${k6_version}" "${system_name}" "${machine_arch}" >&2
    curl --fail --location --silent --show-error \
      --proto '=https' --tlsv1.2 \
      "https://github.com/grafana/k6/releases/download/v${k6_version}/${archive}" \
      --output "${archive_path}"
    verify_checksum "${archive_path}"
  fi

  if [[ "${archive}" == *.zip ]]; then
    unzip -oq "${archive_path}" -d "${tool_root}/unpacked"
  else
    mkdir -p "${tool_root}/unpacked"
    tar -xzf "${archive_path}" -C "${tool_root}/unpacked"
  fi
  extracted="$(find "${tool_root}/unpacked" -type f -name k6 -perm -u+x -print -quit)"
  [[ -n "${extracted}" ]] || {
    printf 'Pinned k6 archive did not contain an executable.\n' >&2
    exit 1
  }
  cp "${extracted}" "${binary_path}"
  chmod 0755 "${binary_path}"
fi

"${binary_path}" version | grep -Fq "k6 v${k6_version}" || {
  printf 'Cached k6 binary does not report v%s.\n' "${k6_version}" >&2
  exit 1
}

exec "${binary_path}" "$@"
