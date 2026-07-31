#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${repo_root}"
export UV_CACHE_DIR="${repo_root}/.cache/uv"

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required. Install it from https://docs.astral.sh/uv/ and retry.\n' >&2
  exit 1
fi

uv python install 3.12
uv sync --frozen --python 3.12
printf 'Locked Python test environment is ready.\n'
