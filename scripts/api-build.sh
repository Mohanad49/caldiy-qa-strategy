#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_sha="1c193cca8682b33b9866c792186033f7ef886682"
image_name="caldiy-api-v2:6.2.0-local"
build_log_dir="${repo_root}/.cache/api-build"

for command_name in docker git tee; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  fi
done

if ! docker info >/dev/null 2>&1; then
  printf 'Docker is not reachable. Start Docker Desktop and try again.\n' >&2
  exit 1
fi

docker_arch="$(docker info --format '{{.Architecture}}')"
if [[ "${docker_arch}" != "x86_64" && "${docker_arch}" != "amd64" ]]; then
  printf 'The Cal.diy v6.2.0 API build targets amd64; Docker reports %s.\n' "${docker_arch}" >&2
  exit 1
fi

source_dir="$(${repo_root}/scripts/api-source.sh)"
mkdir -p "${build_log_dir}"

if [[ -f "${repo_root}/.env" ]]; then
  "${repo_root}/scripts/compose.sh" --profile api down
fi

build_image() {
  local heap_mb="$1"
  local log_file="${build_log_dir}/heap-${heap_mb}.log"

  printf 'Building private local API v2 image with a %s MB Node heap...\n' "${heap_mb}"
  set +e
  docker build \
    --platform linux/amd64 \
    --file "${repo_root}/infra/api-v2.Dockerfile" \
    --tag "${image_name}" \
    --build-arg "API_BUILD_HEAP_MB=${heap_mb}" \
    --build-arg "CALDIY_SOURCE_SHA=${source_sha}" \
    --build-arg 'DATABASE_DIRECT_URL=postgresql://caldiy:build-only@postgres:5432/caldiy' \
    --build-arg 'DATABASE_URL=postgresql://caldiy:build-only@postgres:5432/caldiy' \
    --progress plain \
    "${source_dir}" 2>&1 | tee "${log_file}"
  local build_status="${PIPESTATUS[0]}"
  set -e
  return "${build_status}"
}

if build_image 8192; then
  accepted_heap=8192
else
  first_log="${build_log_dir}/heap-8192.log"
  if grep -Eqi '(exit code: 137|signal: killed|killed$|out of memory|heap out of memory)' "${first_log}"; then
    printf 'The 8192 MB build exhausted Docker memory; retrying once with 6144 MB.\n' >&2
    if build_image 6144; then
      accepted_heap=6144
    else
      printf 'The 6144 MB fallback build failed. Phase 2 cannot continue.\n' >&2
      exit 1
    fi
  else
    printf 'The 8192 MB build failed for a reason other than memory exhaustion; no fallback attempted.\n' >&2
    exit 1
  fi
fi

built_revision="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "${image_name}")"
built_heap="$(docker image inspect --format '{{index .Config.Labels "io.caldiy.qa.build-heap-mb"}}' "${image_name}")"
if [[ "${built_revision}" != "${source_sha}" || "${built_heap}" != "${accepted_heap}" ]]; then
  printf 'Built image provenance labels do not match the accepted build.\n' >&2
  exit 1
fi

printf 'Built %s from %s with a %s MB heap. This image must not be pushed.\n' \
  "${image_name}" "${source_sha}" "${accepted_heap}"
