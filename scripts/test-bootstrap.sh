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

if ! command -v pnpm >/dev/null 2>&1; then
  printf 'pnpm is required for Phase 3 browser tests.\n' >&2
  exit 1
fi
pnpm install --frozen-lockfile
pnpm exec playwright install chromium firefox
printf 'Locked Python and browser test environments are ready.\n'
