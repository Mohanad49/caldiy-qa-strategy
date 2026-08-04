# DEFECT-002 — Default booking-field schemas declare a boolean as an object

## Status

- **Severity:** Medium
- **Upstream eligibility:** Reproduced on current public Cal.diy `main`
- **Duplicate search:** No matching issue or pull request found on 2026-08-04
- **Upstream issue:** [calcom/cal.diy#29904](https://github.com/calcom/cal.diy/issues/29904), open as of 2026-08-04

## Summary

Seven default booking-field output components declare `isDefault` as
`type: object` in the generated OpenAPI document. The same schemas describe the
property as always true and give it boolean `example` and `default` values.
Current source types and the response transformer also emit boolean `true`.

A strict response validator rejects normal default booking fields, and a
generated client can expose the property with an object type that contradicts
the API source and runtime transformation.

## Environment

- Repository: public `calcom/cal.diy`
- Branch: `main`
- Commit: `8418db70c71e5364e6baf26275aafa10e6bc9bd7`
- OpenAPI: `docs/api-reference/v2/openapi.json`
- Response validator: `jsonschema==4.26.0`
- Audit date: 2026-08-04
- Hosted Cal.com: not tested

## Preconditions

- Python 3.12 and `jsonschema==4.26.0` are available.
- The public OpenAPI document from the exact commit above is downloaded as
  `openapi.json`.

## Steps to reproduce

1. Read
   `components.schemas.EmailDefaultFieldOutput_2024_06_14.properties.isDefault`
   from `openapi.json`.
2. Observe `type: object`, `example: true`, and `default: true` on the same
   property.
3. Validate this ordinary field against
   `EmailDefaultFieldOutput_2024_06_14`:

```json
{
  "type": "email",
  "label": "Email",
  "placeholder": "you@example.com",
  "isDefault": true,
  "slug": "email",
  "required": true,
  "hidden": false,
  "disableOnPrefill": false
}
```

4. Compare the schema with the current output class and transformer, both of
   which define or return `isDefault = true` as a boolean.

## Expected result

`isDefault` is documented as a boolean constrained to `true`, and the sample
default booking field validates against the published response schema.

## Actual result

Validation rejects the field because `true` is not of type `object`. The same
contradiction appears in these seven components:

- `EmailDefaultFieldOutput_2024_06_14`
- `GuestsDefaultFieldOutput_2024_06_14`
- `LocationDefaultFieldOutput_2024_06_14`
- `NameDefaultFieldOutput_2024_06_14`
- `NotesDefaultFieldOutput_2024_06_14`
- `RescheduleReasonDefaultFieldOutput_2024_06_14`
- `TitleDefaultFieldOutput_2024_06_14`

## Severity justification

Medium. Event-type response validation and generated client types are affected
across several normal default fields. The source transformer is internally
consistent and there is no evidence here that web booking itself fails, so
classifying this as High would conflate a contract defect with a booking outage.

## Evidence

The current output classes annotate `isDefault` with `@IsBoolean()` and assign
boolean `true`, for example
[Name and Email default outputs](https://github.com/calcom/cal.diy/blob/8418db70c71e5364e6baf26275aafa10e6bc9bd7/packages/platform/types/event-types/event-types_2024_06_14/outputs/booking-fields.output.ts#L26-L90).
The current transformer returns boolean `true` for the same fields, including
[name and email](https://github.com/calcom/cal.diy/blob/8418db70c71e5364e6baf26275aafa10e6bc9bd7/apps/api/v2/src/platform/event-types/event-types_2024_06_14/transformers/internal-to-api/booking-fields.ts#L36-L77).

## Suspected root cause

Inference: the generated Swagger metadata is losing the reflected boolean type
for properties initialized in derived output classes. Adding an explicit
`type: Boolean` (and, if supported, a literal constraint) to the affected
`@ApiProperty` declarations would make generation independent of reflection
behavior. The exact fix should be verified against all default-field variants,
including variants that already generate the correct boolean schema.
