# API v2 runtime qualification

## Status

Runtime qualification is pending. This document describes the acceptance boundary; it will not claim a working API until the complete stack passes the checks below.

## Provenance and use boundary

The API is built locally from Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682`. `scripts/api-source.sh` fetches that exact public commit into ignored `.cache/cal-diy-v6.2.0` and rejects a different commit, remote or dirty checkout before every build.

The upstream `apps/api/v2/package.json` declares the package `UNLICENSED` and private. The resulting `caldiy-api-v2:6.2.0-local` image is therefore only a private local test runtime. It is labelled with the source revision, heap used for the build and `io.caldiy.qa.redistributable=false`. It must not be pushed to Docker Hub, GHCR or another registry.

## Build policy

The build mirrors the upstream sequence but pins the builder to `node:20.19.5-alpine3.22` by digest. It first uses the upstream 8192 MB Node heap while the Compose stack is stopped. A single 6144 MB retry is allowed only when the first log shows memory exhaustion. Any other failure stops Phase 2.

Build logs stay under ignored `.cache/api-build`. The accepted image must report both the controlled source SHA and the successful heap through OCI labels.

## Runtime boundary

The `api` Compose profile adds the local API image and an internal-only, digest-pinned Redis service. API v2 binds only to `127.0.0.1:5555` and shares the Phase 1 PostgreSQL, Mailpit, web, authentication and encryption configuration.

`NODE_ENV=development` is used only because this historical application generates `/docs-json` at startup in that mode. The container still runs the compiled upstream `start:prod` command.

The upstream README instructs local developers to create a fixed `Deployment` record with zero UUID license key and the agreement timestamp `2023-05-15 21:39:47.611`. `scripts/api-license.sh` makes that one record idempotently through direct SQL and refuses to overwrite a different key. This is a narrow bootstrap exception; test fixtures use supported APIs.

On 2026-07-31, the historical `https://goblin.cal.com/v1/license/<key>` check returned HTTP 404 for that documented zero key. The profile therefore sets the upstream `IS_E2E=true` switch, whose API v2 implementation bypasses the external license lookup and uses synchronous slot calculation. This avoids inventing a replacement license service. It also means this environment does not test license enforcement or billing behavior.

## Acceptance checks

The runtime is accepted only when all of these are observed together:

- PostgreSQL, Mailpit, Cal.diy web, Redis and API v2 are healthy.
- `/health` and `/docs-json` return HTTP 200.
- `/v2/me` identifies `owner1-acme@example.com` when called with the upstream seed API key.
- The complete stack remains healthy for ten minutes.
- Total Docker memory for the five project containers remains below 7 GiB throughout that window.

The API build remains local even after qualification. Failure of either permitted build heap, health, authentication, stability or memory acceptance stops Phase 2 rather than substituting API v1 or hosted Cal.com.
