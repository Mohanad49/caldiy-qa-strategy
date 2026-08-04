# F-013 — Booking list rejects null description and location fields

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

`GET /v2/bookings` returns official seed bookings with `description: null`, `meetingUrl: null`, and `location: null`. `BookingOutput_2024_08_13` declares all three as strings when present; `description` and `location` are also required. The generated schemas do not permit the runtime nulls.

## Impact

One older or integration-free booking can make a strictly validated booking list unusable even when newly created bookings contain strings in those fields.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection adds OpenAPI 3.0 nullability only to the three exact tagged field schemas, including their examples, deprecation flag, and description where applicable. F-013 is reported only when those original fields reject `null`, and the complete repaired response must validate.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
