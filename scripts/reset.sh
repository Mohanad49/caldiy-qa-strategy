#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
expected_confirmation="caldiy-qa-strategy"

if [[ "${CONFIRM:-}" != "${expected_confirmation}" ]]; then
  printf 'Refusing reset. Re-run with CONFIRM=%s.\n' "${expected_confirmation}" >&2
  exit 2
fi

"${repo_root}/scripts/compose.sh" down --volumes --remove-orphans
"${repo_root}/scripts/bootstrap.sh"
