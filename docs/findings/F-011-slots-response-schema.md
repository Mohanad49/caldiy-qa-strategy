# F-011 — Slots response schema loses its envelope and item shape

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

The `GET /v2/slots` 200 schema applies each date-keyed slot map directly to the response root through two `oneOf` branches. A successful runtime response instead has the standard `status` and `data` envelope, with the date-keyed map inside `data`. The default branch also declares each array item as a string although the tagged `Slot_2024_09_04` source class and runtime use an object with a required `start` timestamp. Range-format items contain required `start` and `end` timestamps.

The controller contains a hand-written response schema whose examples show the envelope and object items, but its structural keywords describe a different shape.

## Impact

Strict clients reject every normal slots response before callers can discover availability.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection activates only for the exact two titled branches from the tagged controller. It restores the standard success envelope and validates each date value as an array of time or range slot objects. F-011 is reported only when the original union rejects a successful response with an object-valued `data` field, and the complete repaired response must validate.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
