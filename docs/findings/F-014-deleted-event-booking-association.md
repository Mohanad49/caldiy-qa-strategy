# F-014 — Deleted event types null required booking associations

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

The supported API sequence of cancelling a booking and then deleting its event type leaves the historical booking available through booking get/list. Those responses contain `eventTypeId: null` and `eventType: null`. `BookingOutput_2024_08_13` requires both properties and declares non-null number and object schemas.

## Impact

A valid cleanup or event-retirement workflow makes later booking history responses fail strict contract validation.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection adds nullability only to the exact deprecated `eventTypeId` schema and adds a null branch only to the exact `EventType` reference under `eventType`. F-014 is reported only when either original field rejects `null`, and the complete repaired response must validate.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
