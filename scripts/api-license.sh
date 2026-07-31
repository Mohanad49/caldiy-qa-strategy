#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${repo_root}/.env"
compose=("${repo_root}/scripts/compose.sh")

if [[ ! -f "${env_file}" ]]; then
  printf 'Missing %s. Run make sut-bootstrap first.\n' "${env_file}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${env_file}"
set +a

"${compose[@]}" exec -T postgres psql \
  -v ON_ERROR_STOP=1 \
  -U "${POSTGRES_USER}" \
  -d "${POSTGRES_DB}" \
  -c 'DO $license$ DECLARE current_key TEXT; BEGIN SELECT "licenseKey" INTO current_key FROM "Deployment" WHERE id = 1; IF NOT FOUND THEN INSERT INTO "Deployment" (id, "logo", "theme", "licenseKey", "agreedLicenseAt") VALUES (1, NULL, NULL, '\''00000000-0000-0000-0000-000000000000'\'', TIMESTAMP '\''2023-05-15 21:39:47.611'\''); ELSIF current_key IS DISTINCT FROM '\''00000000-0000-0000-0000-000000000000'\'' THEN RAISE EXCEPTION '\''Refusing to overwrite existing Deployment license key'\''; END IF; END $license$;' \
  >/dev/null

printf 'Verified the upstream-documented local Deployment license record.\n'
