# F-012 — Optional booking fields reject runtime nulls

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Normal booking creation returns `rescheduledByEmail: null` and `rating: null` before either value exists. `BookingOutput_2024_08_13` marks both properties optional, but their generated schemas allow only string and number values respectively when the properties are present. Neither schema is nullable.

## Impact

Strict clients reject an ordinary capacity-one booking immediately after successful creation.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection adds OpenAPI 3.0 nullability only to the exact `rescheduledByEmail` string schema with the tagged example and the exact `rating` number schema with the tagged example. F-012 is reported only when either original field rejects `null`, and the complete repaired response must validate.

## Filing policy

Phase 6 must reproduce the mismatch against current Cal.diy and search for duplicate reports before any upstream filing. Until then it remains a versioned local compatibility finding.
