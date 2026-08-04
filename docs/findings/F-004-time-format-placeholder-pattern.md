# F-004 — Schedule time schema contains a placeholder pattern

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Schedule availability and override schemas use the literal JSON Schema pattern `TIME_FORMAT_HH_MM` for `startTime` and `endTime`. That string is not an `HH:MM` regular expression, so a valid runtime value such as `09:00` fails response validation.

The affected pattern appears in the pinned OpenAPI components for schedule availability and overrides. The document hash still matches the controlled upstream snapshot.

## Impact

Standards-aware clients can reject valid schedule responses or generate incorrect validation logic for time fields.

## Automation policy

The response validator classifies only a `pattern` failure on a `startTime` or `endTime` leaf where the schema pattern is exactly `TIME_FORMAT_HH_MM` and the actual value independently matches a strict 24-hour `HH:MM` expression. It emits `KnownContractDeviationWarning`, links the event to F-004, and records it in the per-worker contract report. Invalid time strings and all other patterns still fail validation.

## Filing policy

The Phase 6 current-main audit found no literal `TIME_FORMAT_HH_MM` pattern at
commit `8418db70c71e5364e6baf26275aafa10e6bc9bd7`. This historical compatibility
finding was not filed upstream because its faulty contract condition is no
longer present. See `docs/defects/README.md`.
