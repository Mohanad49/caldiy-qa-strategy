#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"
env_example="${repo_root}/.env.example"
compose=("${repo_root}/scripts/compose.sh")

for command_name in docker openssl curl; do
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
  printf 'Cal.diy v6.2.0 publishes an amd64 runtime; Docker reports %s.\n' "${docker_arch}" >&2
  exit 1
fi

if [[ ! -f "${env_file}" ]]; then
  umask 077
  postgres_password="$(openssl rand -hex 24)"
  nextauth_secret="$(openssl rand -hex 32)"
  encryption_key="$(openssl rand -hex 16)"

  sed \
    -e "s/__POSTGRES_PASSWORD__/${postgres_password}/" \
    -e "s/__NEXTAUTH_SECRET__/${nextauth_secret}/" \
    -e "s/__CALENDSO_ENCRYPTION_KEY__/${encryption_key}/" \
    "${env_example}" > "${env_file}"
  printf 'Created ignored local configuration: %s\n' "${env_file}"
fi

if grep -q '__[A-Z_]*__' "${env_file}"; then
  printf '%s still contains placeholder values; remove it and rerun bootstrap.\n' "${env_file}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

"${compose[@]}" up -d postgres mailpit caldiy

wait_for_health() {
  local service="$1"
  local timeout_seconds="$2"
  local started_at container_id status
  started_at="$(date +%s)"

  while true; do
    container_id="$("${compose[@]}" ps -q "${service}")"
    status=""
    if [[ -n "${container_id}" ]]; then
      status="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "${container_id}")"
    fi

    if [[ "${status}" == "healthy" || "${status}" == "running" ]]; then
      return 0
    fi
    if [[ "${status}" == "unhealthy" || "${status}" == "exited" || "${status}" == "dead" ]]; then
      "${compose[@]}" logs --tail 100 "${service}" >&2
      printf 'Service %s entered state %s.\n' "${service}" "${status}" >&2
      return 1
    fi
    if (( $(date +%s) - started_at >= timeout_seconds )); then
      "${compose[@]}" logs --tail 100 "${service}" >&2
      printf 'Timed out waiting for %s to become healthy.\n' "${service}" >&2
      return 1
    fi
    sleep 3
  done
}

wait_for_health postgres 180
wait_for_health mailpit 180
wait_for_health caldiy 600

seeded="$("${compose[@]}" exec -T postgres \
  psql -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -tAc \
  "SELECT 1 FROM users WHERE email = 'pro@example.com' LIMIT 1;")"

if [[ "${seeded}" == "1" ]]; then
  printf 'Official Cal.diy fixtures already exist; skipping seed.\n'
else
  printf 'Loading Cal.diy official development fixtures...\n'
  "${compose[@]}" exec -T caldiy yarn workspace @calcom/prisma db-seed
fi

"${repo_root}/scripts/smoke.sh"

printf '\nCal.diy:  http://localhost:%s\n' "${CALDIY_WEB_PORT}"
printf 'Booking:  http://localhost:%s/pro/30min\n' "${CALDIY_WEB_PORT}"
printf 'Mailpit:  http://localhost:%s\n' "${MAILPIT_HTTP_PORT}"
printf 'Fixture:  pro@example.com / pro (local development only)\n'
