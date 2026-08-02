#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_sha="1c193cca8682b33b9866c792186033f7ef886682"
image_name="caldiy-api-v2:6.2.0-local"
source_dir="${repo_root}/.cache/cal-diy-v6.2.0"
cache_scope="caldiy-api-v2-amd64-v6.2.0"
requested_heap="${CI_API_BUILD_HEAP_MB:-}"
load_image="${CI_API_BUILD_LOAD:-true}"
write_cache="${CI_API_CACHE_WRITE:-false}"
log_dir="${repo_root}/.cache/ci-api-build"

[[ "${CI:-}" == "true" ]] || {
  printf 'ci-api-build.sh is restricted to CI; use make api-build locally.\n' >&2
  exit 1
}
[[ -d "${source_dir}/.git" ]] || {
  printf 'Missing exact-source checkout at %s.\n' "${source_dir}" >&2
  exit 1
}
[[ "$(git -C "${source_dir}" rev-parse HEAD)" == "${source_sha}" ]] || {
  printf 'CI source checkout does not match %s.\n' "${source_sha}" >&2
  exit 1
}
[[ -z "$(git -C "${source_dir}" status --short)" ]] || {
  printf 'CI source checkout is dirty.\n' >&2
  exit 1
}
docker buildx inspect --bootstrap | grep -E '^Driver:[[:space:]]+docker-container$' >/dev/null || {
  printf 'The CI API build requires the Buildx docker-container driver.\n' >&2
  exit 1
}
[[ "${load_image}" == "true" || "${load_image}" == "false" ]] || {
  printf 'CI_API_BUILD_LOAD must be true or false.\n' >&2
  exit 2
}
[[ "${write_cache}" == "true" || "${write_cache}" == "false" ]] || {
  printf 'CI_API_CACHE_WRITE must be true or false.\n' >&2
  exit 2
}
[[ "${load_image}" == "true" || "${write_cache}" == "true" ]] || {
  printf 'A CI API build must load the image, write the cache, or both.\n' >&2
  exit 2
}

mkdir -p "${log_dir}"

build_image() {
  local heap_mb="$1"
  local log_file="${log_dir}/heap-${heap_mb}.log"
  local -a outputs=()
  if [[ "${write_cache}" == "true" ]]; then
    outputs+=(--cache-to "type=gha,scope=${cache_scope},mode=max")
  fi
  if [[ "${load_image}" == "true" ]]; then
    outputs+=(--load)
  fi
  printf 'Building non-distributable API v2 with %s MB heap (load=%s, cache-write=%s).\n' \
    "${heap_mb}" "${load_image}" "${write_cache}"
  set +e
  docker buildx build \
    --platform linux/amd64 \
    --file "${repo_root}/infra/api-v2.Dockerfile" \
    --tag "${image_name}" \
    --build-arg "API_BUILD_HEAP_MB=${heap_mb}" \
    --build-arg "CALDIY_SOURCE_SHA=${source_sha}" \
    --build-arg 'DATABASE_DIRECT_URL=postgresql://caldiy:build-only@postgres:5432/caldiy' \
    --build-arg 'DATABASE_URL=postgresql://caldiy:build-only@postgres:5432/caldiy' \
    --cache-from "type=gha,scope=${cache_scope}" \
    "${outputs[@]}" \
    --progress plain \
    "${source_dir}" 2>&1 | tee "${log_file}"
  local status="${PIPESTATUS[0]}"
  set -e
  return "${status}"
}

if [[ -n "${requested_heap}" ]]; then
  [[ "${requested_heap}" == "8192" || "${requested_heap}" == "6144" ]] || {
    printf 'CI_API_BUILD_HEAP_MB must be 8192 or 6144.\n' >&2
    exit 2
  }
  build_image "${requested_heap}" || exit 1
  accepted_heap="${requested_heap}"
elif build_image 8192; then
  accepted_heap=8192
else
  first_log="${log_dir}/heap-8192.log"
  if grep -Eqi '(exit code: 137|signal: killed|killed$|out of memory|heap out of memory)' \
    "${first_log}"; then
    printf 'The 8192 MB CI build exhausted runner memory; retrying once with 6144 MB.\n' >&2
    build_image 6144 || {
      printf 'The permitted 6144 MB fallback also failed.\n' >&2
      exit 1
    }
    accepted_heap=6144
  else
    printf 'The 8192 MB CI build failed for a non-memory reason; fallback is forbidden.\n' >&2
    exit 1
  fi
fi

if [[ "${load_image}" == "true" ]]; then
  built_revision="$(docker image inspect --format '{{index .Config.Labels "org.opencontainers.image.revision"}}' "${image_name}")"
  built_heap="$(docker image inspect --format '{{index .Config.Labels "io.caldiy.qa.build-heap-mb"}}' "${image_name}")"
  redistributable="$(docker image inspect --format '{{index .Config.Labels "io.caldiy.qa.redistributable"}}' "${image_name}")"
  [[ "${built_revision}" == "${source_sha}" && "${built_heap}" == "${accepted_heap}" ]] || {
    printf 'Loaded CI image provenance labels do not match the accepted build.\n' >&2
    exit 1
  }
  [[ "${redistributable}" == "false" ]] || {
    printf 'Loaded CI image lost its non-redistributable label.\n' >&2
    exit 1
  }
else
  docker image inspect "${image_name}" >/dev/null 2>&1 && {
    printf 'Cache-only CI build unexpectedly loaded %s.\n' "${image_name}" >&2
    exit 1
  }
fi

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  printf 'heap_mb=%s\n' "${accepted_heap}" >> "${GITHUB_OUTPUT}"
fi
printf 'Accepted CI API build heap: %s MB (load=%s, cache-write=%s).\n' \
  "${accepted_heap}" "${load_image}" "${write_cache}"
