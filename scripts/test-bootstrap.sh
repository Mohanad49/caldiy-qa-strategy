#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
node_version="$(<"${repo_root}/.nvmrc")"
node_candidate="${NVM_DIR:-${HOME}/.nvm}/versions/node/v${node_version}/bin"

if [[ -x "${node_candidate}/node" ]]; then
  export PATH="${node_candidate}:${PATH}"
fi
if [[ "$(node --version)" != "v${node_version}" ]]; then
  printf 'Node %s is required for browser tests; found %s.\n' "${node_version}" "$(node --version)" >&2
  exit 1
fi
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
