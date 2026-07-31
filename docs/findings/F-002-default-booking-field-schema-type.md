# F-002 — Default booking-field schemas use the wrong type

## Status and boundary

Open local compatibility finding. Observed in the canonical and runtime OpenAPI documents for Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682`. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Several `*DefaultFieldOutput_2024_06_14` component schemas declare `isDefault` as `type: object` while their description says the property is always true and both `example` and `default` are boolean `true`. `openapi-spec-validator` rejects the suite-surface document because the boolean annotation does not match the declared object type.

Examples include `EmailDefaultFieldOutput_2024_06_14`, `NameDefaultFieldOutput_2024_06_14`, `LocationDefaultFieldOutput_2024_06_14`, `RescheduleReasonDefaultFieldOutput_2024_06_14`, `TitleDefaultFieldOutput_2024_06_14`, `NotesDefaultFieldOutput_2024_06_14`, and `GuestsDefaultFieldOutput_2024_06_14`.

## Reproduction

1. Verify the pinned OpenAPI SHA-256 is `e9e662d1183733ee57da8ac02a60891c67e021df47c30b4d6fd29bdad60a0cfb`.
2. Build a reduced OpenAPI document containing the Phase 2 operations and their referenced components.
3. Validate it with `openapi-spec-validator` 0.9.0.
4. Observe `OpenAPIValidationError: True is not of type 'object'` for the `isDefault` schema.

`make contracts-verify` automates those checks and reports this known annotation failure. It also validates an annotation-free structural projection, while individual HTTP responses are evaluated separately against the unmodified pinned operation schemas.

## Impact

Schema generators and validators can reject the document or generate an object-shaped `isDefault` property even though the API model describes a boolean. This affects event-type response dependencies used by the Phase 2 surface.

## Filing policy

Phase 6 must reproduce the mismatch against current Cal.diy and search for duplicate reports before any upstream filing. Until then it remains a versioned local compatibility finding.
