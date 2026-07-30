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
  infra/compose.yml
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
  config --quiet

image_count=0
while IFS= read -r image_ref; do
  image_count=$((image_count + 1))
  [[ "${image_ref}" == *@sha256:* ]] || fail "image is not digest-pinned: ${image_ref}"
  [[ "${image_ref}" != *:latest* ]] || fail "latest image tag is forbidden: ${image_ref}"
done < <(sed -n 's/^[[:space:]]*image:[[:space:]]*//p' infra/compose.yml)
[[ "${image_count}" -eq 3 ]] || fail "expected exactly three Phase 1 images"

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

if git grep -nE '(sk_live_[A-Za-z0-9]+|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|-----BEGIN (RSA |OPENSSH |EC )?PRIVATE KEY-----)' \
  -- . ':(exclude).env.example'; then
  fail 'probable secret found in tracked content'
fi

if git grep -nE '__[A-Z_]+__' -- . \
  ':(exclude).env.example' \
  ':(exclude)scripts/bootstrap.sh'; then
  fail 'unresolved placeholder found outside .env.example'
fi

git diff --check
make help >/dev/null

printf 'Phase 1 static validation passed.\n'
