# F-010 — Event-type users are documented as strings

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

`EventTypeOutput_2024_06_14.users` is emitted into the OpenAPI document as an array of strings. The runtime returns the structured `User_2024_06_14` objects defined by the same tagged source: `id`, `name`, `username`, `avatarUrl`, `weekStart`, `brandColor`, `darkBrandColor`, and `metadata`.

The source property uses `@DocsProperty()` without an explicit array item type even though its TypeScript type and class-transformer metadata identify `User_2024_06_14[]`. The generated document therefore loses the object schema.

## Impact

Generated or strictly validated clients reject normal event-type responses at the first user entry.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection replaces the item type only when a property named `users` is exactly an array whose items are declared as strings. The replacement schema mirrors the eight fields and nullability in the tagged `User_2024_06_14` source class. F-010 is reported only for object entries rejected by the original string item type, and the complete repaired response must validate.

## Filing policy

The same schema condition remains in the Phase 6 current-main audit, but the
current runtime response was not reproduced. This historical finding remains
local and was not filed upstream. See `docs/defects/README.md`.
