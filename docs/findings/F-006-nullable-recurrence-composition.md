# F-006 — Nullable recurrence composition rejects null

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Event-type output schemas describe `recurrence` as `nullable: true` with a single `allOf` reference to the non-nullable object schema `Recurrence_2024_06_14`. The runtime normally returns `recurrence: null` for non-recurring event types. OpenAPI 3.0 validation does not propagate the wrapper's nullable intent through the referenced `allOf` object, so the actual response fails as “None for not nullable.”

## Impact

Strict clients reject ordinary non-recurring event-type responses even though null is the runtime's normal representation and the wrapper appears intended to allow it.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection changes only a nullable, single-reference `allOf` whose reference ends in `Recurrence_2024_06_14` into an `anyOf` containing the original reference and a null-only branch. F-006 is accepted only when the full response then validates; the warning and evidence remain visible in the per-worker contract report.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
