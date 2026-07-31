#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"
env_example="${repo_root}/.env.example"

for command_name in openssl sed grep; do
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    printf 'Required command is missing: %s\n' "${command_name}" >&2
    exit 1
  fi
done

if [[ ! -f "${env_file}" ]]; then
  umask 077
  postgres_password="$(openssl rand -hex 24)"
  nextauth_secret="$(openssl rand -hex 32)"
  encryption_key="$(openssl rand -hex 16)"
  api_jwt_secret="$(openssl rand -hex 32)"
  service_account_key="$(openssl rand -hex 16)"

  sed \
    -e "s/__POSTGRES_PASSWORD__/${postgres_password}/" \
    -e "s/__NEXTAUTH_SECRET__/${nextauth_secret}/" \
    -e "s/__CALENDSO_ENCRYPTION_KEY__/${encryption_key}/" \
    -e "s/__API_V2_JWT_SECRET__/${api_jwt_secret}/" \
    -e "s/__CALCOM_SERVICE_ACCOUNT_ENCRYPTION_KEY__/${service_account_key}/" \
    "${env_example}" > "${env_file}"
  printf 'Created ignored local configuration: %s\n' "${env_file}"
fi

ensure_env_key() {
  local key="$1"
  local value="$2"
  if ! grep -q "^${key}=" "${env_file}"; then
    umask 077
    printf '\n%s=%s\n' "${key}" "${value}" >> "${env_file}"
    printf 'Added missing local configuration key: %s\n' "${key}"
  fi
}

# Extend Phase 1 .env files without changing existing database or web secrets.
ensure_env_key CALDIY_API_PORT 5555
ensure_env_key API_V2_JWT_SECRET "$(openssl rand -hex 32)"
ensure_env_key CALCOM_SERVICE_ACCOUNT_ENCRYPTION_KEY "$(openssl rand -hex 16)"
ensure_env_key CALCOM_LICENSE_KEY 00000000-0000-0000-0000-000000000000
ensure_env_key CALDIY_API_KEY cal_0123456789abcdef0123456789abcdef
ensure_env_key STRIPE_API_KEY sk_test_local_caldiy_qa_only
ensure_env_key STRIPE_WEBHOOK_SECRET whsec_local_caldiy_qa_only

if grep -q '__[A-Z_]*__' "${env_file}"; then
  printf '%s still contains placeholder values; remove it and rerun bootstrap.\n' "${env_file}" >&2
  exit 1
fi
