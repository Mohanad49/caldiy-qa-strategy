# Phase 6 defect register

## Product boundary

This register distinguishes three different evidence classes:

1. Cal.diy `v6.2.0` findings reproduced by this repository's controlled local
   suites;
2. contract defects reproduced against the current public Cal.diy `main`
   source and OpenAPI document; and
3. hosted Cal.com, which was not tested and is not covered by any report here.

The current-main audit was run on 2026-08-04 at commit
`8418db70c71e5364e6baf26275aafa10e6bc9bd7`. `make defects-audit` fetches public
`main`, records the exact commit and OpenAPI SHA-256, and writes ignored JSON
and Markdown evidence under `test-results/defects/current-main/`.

## Upstream-eligible reports

| ID | Summary | Severity | Current reproduction | Duplicate search | Upstream status |
|---|---|---:|---|---|---|
| [DEFECT-001](DEFECT-001-duplicate-openapi-operation-ids.md) | Deprecated calendar aliases produce duplicate OpenAPI operation IDs | Medium | Public `main` source and OpenAPI | No matching issue or pull request found on 2026-08-04 | [calcom/cal.diy#29903](https://github.com/calcom/cal.diy/issues/29903) |
| [DEFECT-002](DEFECT-002-default-booking-field-type.md) | Seven default booking-field schemas declare a boolean as an object | Medium | Public `main` source and OpenAPI | No matching issue or pull request found on 2026-08-04 | [calcom/cal.diy#29904](https://github.com/calcom/cal.diy/issues/29904) |

These are API-contract defects in current public Cal.diy. They are not claims
about the current hosted Cal.com service. Severity is Medium because both can
break strict validators, SDK generation, or generated client behavior, but
neither has evidence of preventing an ordinary booking in the web UI.

## Historical finding triage

The detailed `v6.2.0` observations remain in [`docs/findings`](../findings/).
They are not silently relabelled as current defects. The current audit produced
this disposition:

| Finding | `v6.2.0` evidence | Current public `main` disposition | Upstream filing |
|---|---|---|---|
| CALDIY-LOCAL-001 | Cairo repeated-hour slot omission | Current runtime not reproduced | Not eligible |
| CALDIY-LOCAL-002 | Calendar switch lacks an accessible name | Current UI not reproduced | Not eligible |
| CALDIY-LOCAL-003 | Guest-details contrast failures | Current UI not reproduced | Not eligible |
| CALDIY-LOCAL-004 | Terms/privacy link distinction | Current UI not reproduced | Not eligible |
| F-001 | Unresolved `orgId` path parameter | Affected route is absent | Not filed; no longer present |
| F-002 | Default-field `isDefault` type mismatch | Reproduced in current source and contract as DEFECT-002 | Eligible |
| F-003 | Weekday enum attached to array | Faulty array enum is absent | Not filed; no longer present |
| F-004 | Literal `TIME_FORMAT_HH_MM` pattern | Placeholder pattern is absent | Not filed; no longer present |
| F-005 | Overlapping booking-field `oneOf` branches | Current runtime not reproduced after isolating F-002 | Not eligible yet |
| F-006 | Nullable recurrence composition | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-007 | Forward-redirect boolean documented as object | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-008 | Disabled booking-window shape omitted | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-009 | Disabled seats shape omitted | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-010 | Event-type users documented as strings | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-011 | Slots envelope and item shape mismatch | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-012 | Booking optional fields reject null | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-013 | Booking text fields reject null | Schema condition remains; current runtime not reproduced | Not eligible yet |
| F-014 | Deleted-event booking associations reject null | Schema condition remains; current runtime not reproduced | Not eligible yet |

“Schema condition remains” is deliberately weaker than “current defect
reproduced.” The historical runtime returned the conflicting value, but the
current API runtime was not built and exercised for these reports. A matching
schema shape alone is insufficient evidence for an upstream claim about the
current response.

## Duplicate-search method

Before filing, both open and closed issues and pull requests in
`calcom/cal.diy` were searched with exact identifiers and broader terms:

- `getCalendarEventDetails`, `operationId`, `OpenAPI`, and `duplicate operation id`;
- `isDefault`, `DefaultFieldOutput`, `OpenAPI`, and `booking field`.

Searches returning no match are timestamped evidence, not proof that no
duplicate can exist under unrelated wording. If a maintainer identifies a
duplicate, the report should be closed and linked rather than defended as new.

## Reporting policy

- A report must stand alone without links to this private repository.
- Evidence must name the public commit, tool version, and exact command or
  source comparison.
- Suspected root cause is labelled as an inference.
- Historical-only findings remain local compatibility reports.
- No destructive or high-volume testing targets public infrastructure.
