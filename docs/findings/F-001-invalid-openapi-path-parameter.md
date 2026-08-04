# F-001 — Full OpenAPI document has an unresolved path parameter

## Status and boundary

Open local compatibility finding. Observed against the controlled Cal.diy v6.2.0 snapshot at commit `1c193cca8682b33b9866c792186033f7ef886682` and its locally built API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

The canonical `docs/api-reference/v2/openapi.json` and runtime `/docs-json` both define `GET /v2/organizations/{orgId}/teams/{teamId}` without resolving the `orgId` path parameter. `openapi-spec-validator` 0.9.0 therefore rejects the full document with `UnresolvableParameterError`.

The pinned document still has the expected SHA-256 `e9e662d1183733ee57da8ac02a60891c67e021df47c30b4d6fd29bdad60a0cfb`; this is not file corruption introduced by the QA repository.

## Reproduction

1. Start the qualified API v2 stack with `make sut-api-bootstrap`.
2. Install the locked Python environment with `make test-bootstrap`.
3. Run `make contracts-verify`.
4. Observe that the 18 suite operations match the pinned runtime contract and the command reports the known full-document validation failure for the unresolved `orgId` parameter.

## Impact

Tools that require a globally valid OpenAPI document cannot consume this snapshot without repair or selective validation. The Phase 2 suite does not use the affected organization-team operation, so it validates a reduced document containing only suite-used paths and still validates each response against the pinned operation schema.

## Filing policy

The Phase 6 current-main audit found that the affected route is absent at
commit `8418db70c71e5364e6baf26275aafa10e6bc9bd7`. This historical compatibility
finding was not filed upstream because its faulty contract condition is no
longer present. See `docs/defects/README.md`.
