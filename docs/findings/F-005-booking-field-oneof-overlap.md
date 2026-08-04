# F-005 — Booking-field output union has overlapping branches

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Event-type `bookingFields` items are described with a `oneOf` containing default and custom field output schemas. After correcting the separately recorded F-002 `isDefault` type for validation, an actual default name field validates against multiple branches, including title, notes, guests, and reschedule-reason schemas. Because `oneOf` requires exactly one match, the response remains invalid.

The schemas rely on default-valued fields but do not constrain enough discriminator properties to keep the branches mutually exclusive.

## Impact

Strict clients reject event-type create, list, and read responses containing normal default booking fields. Code generation can also produce an exclusive union that the runtime cannot satisfy.

## Automation policy

The response validator first evaluates the unmodified pinned schema. It then applies the exact F-002/F-003/F-004 repairs and converts `oneOf` to `anyOf` only when every branch is a reference and the union contains a `*DefaultFieldOutput_2024_06_14` component. The original mismatch is accepted only if the complete response passes after those known repairs. F-005 is emitted as a warning and written to the per-worker contract report; unrelated union failures still fail validation.

## Filing policy

The Phase 6 audit did not reproduce the current runtime response after
isolating the separately filed F-002 type defect. This historical compatibility
finding remains local and was not filed upstream. See `docs/defects/README.md`.
