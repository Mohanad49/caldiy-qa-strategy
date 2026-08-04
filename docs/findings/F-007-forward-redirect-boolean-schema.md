# F-007 — Forward-redirect flag is declared as an object

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Event-type output schemas declare `forwardParamsSuccessRedirect` as a nullable object. The runtime returns a boolean flag, including `true` in the official seeded event types. OpenAPI response validation therefore fails with “True is not of type 'object'.”

## Impact

Strict clients reject normal event-type list and detail responses and can generate an object-shaped property for a runtime boolean.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection changes only a property named `forwardParamsSuccessRedirect` whose schema is exactly a nullable object into a nullable boolean. F-007 is accepted only if the complete response validates after all documented exact repairs; the warning and per-worker evidence remain visible.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
