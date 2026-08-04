# F-009 — Seats output omits the disabled shape

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Event-type output schemas describe `seats` only as an active-seat object requiring `seatsPerTimeSlot`, `showAttendeeInfo`, and `showAvailabilityCount`. The runtime returns `{"disabled": true}` for normal capacity-one event types. The input model supports `Disabled_2024_06_14`, but the output schema omits it.

## Impact

Strict clients reject standard event types without seated-event behavior.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection adds `Disabled_2024_06_14` only to a property named `seats` whose schema is exactly the direct `Seats_2024_06_14` reference. F-009 is accepted only for the exact disabled sentinel and only when the complete repaired response validates.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
