#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"

fail() {
  printf 'Validation failed: %s\n' "$1" >&2
  exit 1
}

required_files=(
  README.md
  DECISIONS.md
  docs/TEST-STRATEGY.md
  docs/RISK-ANALYSIS.md
  docs/API-V2-RUNTIME.md
  infra/compose.yml
  infra/api-v2.Dockerfile
  .env.example
)

for required_file in "${required_files[@]}"; do
  [[ -s "${required_file}" ]] || fail "missing or empty ${required_file}"
done

for script in scripts/*.sh; do
  bash -n "${script}" || fail "invalid shell syntax in ${script}"
  [[ -x "${script}" ]] || fail "${script} is not executable"
done

docker compose \
  --project-name caldiy-qa-strategy \
  --env-file .env.example \
  --file infra/compose.yml \
  --profile api \
  config --quiet

image_count=0
local_image_count=0
while IFS= read -r image_ref; do
  image_count=$((image_count + 1))
  if [[ "${image_ref}" == "caldiy-api-v2:6.2.0-local" ]]; then
    local_image_count=$((local_image_count + 1))
  else
    [[ "${image_ref}" == *@sha256:* ]] || fail "external image is not digest-pinned: ${image_ref}"
  fi
  [[ "${image_ref}" != *:latest* ]] || fail "latest image tag is forbidden: ${image_ref}"
done < <(sed -n 's/^[[:space:]]*image:[[:space:]]*//p' infra/compose.yml)
[[ "${image_count}" -eq 5 ]] || fail "expected exactly five Compose images"
[[ "${local_image_count}" -eq 1 ]] || fail "expected exactly one non-distributable local image"

expected_images=(
  'postgres:16-bookworm@sha256:92620daddcd947f8d5ab5ba66e848702fe443d87fed30c4cea8e389fd78dfc55'
  'axllent/mailpit:v1.27.5@sha256:5921fa3c3f0a34eb000a89ac8279d1f9d711e486a9a8fd094f7db5a1920256ab'
  'calcom.docker.scarf.sh/calcom/cal.com:v6.2.0@sha256:ace3bb1219fb7306585ab9f4d94d41af7ee064c343db0498173436bbe857bd49'
  'redis:7.4.10-alpine@sha256:e7723ff73d963f5cc6d9c4643ea3d989527a402a319239054e9472a7fb9219a2'
  'caldiy-api-v2:6.2.0-local'
)
for expected_image in "${expected_images[@]}"; do
  grep -Fq "image: ${expected_image}" infra/compose.yml || fail "missing expected image pin: ${expected_image}"
done

grep -Fxq 'FROM node:20.19.5-alpine3.22@sha256:6178e78b972f79c335df281f4b7674a2d85071aae2af020ffa39f0a770265435' \
  infra/api-v2.Dockerfile || fail 'API v2 builder image pin changed'
grep -Fq '1c193cca8682b33b9866c792186033f7ef886682' scripts/api-source.sh || \
  fail 'API source verifier does not contain the controlled commit'
grep -Fq 'io.caldiy.qa.redistributable="false"' infra/api-v2.Dockerfile || \
  fail 'API local-image redistribution guard label is missing'

required_strategy_headings=(
  '## Product and version boundary'
  '## Risk model'
  '## Test levels and ownership'
  '## Environments'
  '## Test data strategy'
  '## Entry and exit criteria'
  '## Reporting and defect policy'
  '## Explicit exclusions'
)
for heading in "${required_strategy_headings[@]}"; do
  grep -Fxq "${heading}" docs/TEST-STRATEGY.md || fail "missing strategy heading: ${heading}"
done

required_risk_headings=(
  '## Time model and invariants'
  '## Failure catalogue'
  '## Zone matrix'
  '## Deterministic test design'
  '## Boundary scenarios'
  '## Oracle and assertion policy'
)
for heading in "${required_risk_headings[@]}"; do
  grep -Fxq "${heading}" docs/RISK-ANALYSIS.md || fail "missing risk heading: ${heading}"
done

if git grep -nEi 'self-host(ed|able)[[:space:]]+Cal\.com|Cal\.com[[:space:]]+self-host(ed|able)' -- '*.md'; then
  fail 'unqualified self-hosted Cal.com wording found'
fi

if git ls-files --error-unmatch .env >/dev/null 2>&1; then
  fail '.env is tracked'
fi
git check-ignore -q .env || fail '.env is not ignored'
git check-ignore -q .cache/cal-diy-v6.2.0 || fail 'API source cache is not ignored'

if git grep -nE '(sk_live_[A-Za-z0-9]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----)' \
  -- . ':(exclude).env.example'; then
  fail 'probable secret found in tracked content'
fi

if git grep -nE '__[A-Z_]+__' -- . \
  ':(exclude).env.example' \
  ':(exclude)scripts/ensure-env.sh'; then
  fail 'unresolved placeholder found outside .env.example'
fi

git diff --check
make help >/dev/null

printf 'Repository static validation passed.\n'
