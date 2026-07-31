#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
compose=("${repo_root}/scripts/compose.sh")
evidence_dir="${repo_root}/.cache/runtime-qualification"
evidence_file="${evidence_dir}/latest.txt"
services=(postgres mailpit caldiy redis api-v2)
memory_limit_mib=7168
peak_mib=0

mkdir -p "${evidence_dir}"
: > "${evidence_file}"
printf 'started_utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "${evidence_file}"
printf 'duration_seconds=600\ninterval_seconds=30\nmemory_limit_mib=%s\n' "${memory_limit_mib}" >> "${evidence_file}"

baseline_restarts=()
for service in "${services[@]}"; do
  container_id="$(${compose[@]} --profile api ps -q "${service}")"
  if [[ -z "${container_id}" ]]; then
    printf 'Service %s has no running container.\n' "${service}" >&2
    exit 1
  fi
  baseline_restarts+=("$(docker inspect --format '{{.RestartCount}}' "${container_id}")")
done

memory_to_mib() {
  local value="$1"
  local number unit
  number="${value%%[A-Za-z]*}"
  unit="${value#${number}}"
  awk -v number="${number}" -v unit="${unit}" 'BEGIN {
    if (unit == "GiB") factor = 1024;
    else if (unit == "MiB") factor = 1;
    else if (unit == "KiB") factor = 1 / 1024;
    else if (unit == "B") factor = 1 / 1048576;
    else exit 2;
    printf "%.0f", number * factor;
  }'
}

printf 'Monitoring five healthy containers for ten minutes (limit: %s MiB)...\n' "${memory_limit_mib}"
for sample in $(seq 0 20); do
  container_ids=()
  for service_index in "${!services[@]}"; do
    service="${services[${service_index}]}"
    container_id="$(${compose[@]} --profile api ps -q "${service}")"
    status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")"
    restart_count="$(docker inspect --format '{{.RestartCount}}' "${container_id}")"
    if [[ "${status}" != "healthy" ]]; then
      printf 'Service %s is %s during qualification.\n' "${service}" "${status}" >&2
      exit 1
    fi
    if [[ "${restart_count}" != "${baseline_restarts[${service_index}]}" ]]; then
      printf 'Service %s restarted during qualification.\n' "${service}" >&2
      exit 1
    fi
    container_ids+=("${container_id}")
  done

  total_mib=0
  per_container=""
  while IFS='|' read -r name usage; do
    memory_value="${usage%% / *}"
    memory_mib="$(memory_to_mib "${memory_value}")"
    total_mib=$((total_mib + memory_mib))
    per_container+=" ${name}=${memory_mib}MiB"
  done < <(docker stats --no-stream --format '{{.Name}}|{{.MemUsage}}' "${container_ids[@]}")

  if (( total_mib > peak_mib )); then
    peak_mib="${total_mib}"
  fi
  if (( total_mib >= memory_limit_mib )); then
    printf 'Stack memory reached %s MiB; acceptance requires less than %s MiB.\n' \
      "${total_mib}" "${memory_limit_mib}" >&2
    exit 1
  fi

  elapsed_seconds=$((sample * 30))
  printf 'sample=%02d elapsed_seconds=%03d total_mib=%s%s\n' \
    "${sample}" "${elapsed_seconds}" "${total_mib}" "${per_container}" | tee -a "${evidence_file}"
  if (( sample < 20 )); then
    sleep 30
  fi
done

"${repo_root}/scripts/api-smoke.sh" >/dev/null
printf 'completed_utc=%s\npeak_mib=%s\nresult=accepted\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${peak_mib}" >> "${evidence_file}"
printf 'Runtime qualification passed: ten healthy minutes, no restarts, peak %s MiB.\n' "${peak_mib}"
