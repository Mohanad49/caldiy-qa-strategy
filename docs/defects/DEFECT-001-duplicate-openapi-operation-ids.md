# DEFECT-001 — Deprecated calendar aliases produce duplicate OpenAPI operation IDs

## Status

- **Severity:** Medium
- **Upstream eligibility:** Reproduced on current public Cal.diy `main`
- **Duplicate search:** No matching issue or pull request found on 2026-08-04
- **Upstream issue:** [calcom/cal.diy#29903](https://github.com/calcom/cal.diy/issues/29903), open as of 2026-08-04

## Summary

Cal.diy's generated API v2 OpenAPI document assigns the same `operationId` to
each singular/plural alias of two calendar endpoints. The document therefore
contains two copies of `CalUnifiedCalendarsController_getCalendarEventDetails`
and two copies of `CalUnifiedCalendarsController_updateCalendarEvent`.

OpenAPI 3.0 requires each `operationId` to be unique across all operations.
`openapi-spec-validator` rejects the current document at the first duplicate,
and client generators can collide or overwrite methods.

## Environment

- Repository: public `calcom/cal.diy`
- Branch: `main`
- Commit: `8418db70c71e5364e6baf26275aafa10e6bc9bd7`
- OpenAPI: `docs/api-reference/v2/openapi.json`
- Validator: `openapi-spec-validator==0.9.0`
- Audit date: 2026-08-04
- Hosted Cal.com: not tested

## Preconditions

- Python 3.12 is available.
- The public OpenAPI document from the exact commit above is downloaded as
  `openapi.json`.

## Steps to reproduce

1. Install `openapi-spec-validator==0.9.0`.
2. Run `openapi-spec-validator openapi.json`.
3. Enumerate the operation IDs for these four paths:
   - `GET /v2/calendars/{calendar}/events/{eventUid}`
   - `GET /v2/calendars/{calendar}/event/{eventUid}`
   - `PATCH /v2/calendars/{calendar}/events/{eventUid}`
   - `PATCH /v2/calendars/{calendar}/event/{eventUid}`

## Expected result

The document passes OpenAPI validation. Every operation has a unique
`operationId`, including deprecated aliases, or the deprecated aliases are not
emitted as separate documented operations.

## Actual result

Validation stops with:

```text
Operation ID 'CalUnifiedCalendarsController_getCalendarEventDetails' for 'get'
in '/v2/calendars/{calendar}/event/{eventUid}' is not unique
```

The same structural conflict also exists for
`CalUnifiedCalendarsController_updateCalendarEvent` on the two PATCH paths.

## Severity justification

Medium. This does not prove that the HTTP handlers fail at runtime, but it makes
the published contract invalid for a conforming validator and can cause SDK or
client-generation method collisions. The affected surface is API tooling, not
an evidenced outage of the booking UI, so High would overstate impact.

## Evidence

The pinned source applies two paths to one NestJS handler for
[GET aliases](https://github.com/calcom/cal.diy/blob/8418db70c71e5364e6baf26275aafa10e6bc9bd7/apps/api/v2/src/modules/cal-unified-calendars/controllers/cal-unified-calendars.controller.ts#L241-L250)
and
[PATCH aliases](https://github.com/calcom/cal.diy/blob/8418db70c71e5364e6baf26275aafa10e6bc9bd7/apps/api/v2/src/modules/cal-unified-calendars/controllers/cal-unified-calendars.controller.ts#L269-L278).
The singular route is intentionally deprecated, so retaining both HTTP aliases
may be valid; the defect is their duplicated contract identity.

## Suspected root cause

Inference: NestJS Swagger derives an operation ID from the controller method
name. Supplying two route patterns to one decorated method emits two OpenAPI
operations with that same derived identifier. A fix likely needs either a
unique explicit identifier for the deprecated alias or exclusion of that alias
from the generated document while preserving runtime compatibility.
