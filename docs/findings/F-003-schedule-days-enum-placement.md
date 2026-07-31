# F-003 — Schedule weekday enum is applied to the array

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified local API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

The schedule availability response schema defines `days` as an array and correctly constrains each item to a weekday string. It also incorrectly adds the same list of weekday strings as an `enum` on the array itself. An actual value such as `["Monday", "Tuesday"]` is consequently rejected because the array is not equal to any string enum member.

The first observed mismatch came from `POST /v2/schedules` status 201 at `data.availability.0.days` while the fixture CLI created an all-days UTC schedule.

## Impact

Standards-aware response validation rejects otherwise valid schedule responses, affecting schedule create, read, list, update, and dependent fixture creation.

## Automation policy

The response validator still evaluates the unmodified pinned schema. It classifies only an `enum` failure at a `days` leaf where the instance is an array and the schema is an array with a string enum. That exact mismatch is emitted as `KnownContractDeviationWarning`, linked to F-003, and written into the per-worker contract report. Any other validation error still fails the request.

## Filing policy

Phase 6 must reproduce the mismatch against current Cal.diy and search for duplicate reports before any upstream filing. Until then it remains a versioned local compatibility finding.
