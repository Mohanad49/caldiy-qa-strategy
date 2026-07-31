# F-008 — Booking-window output omits the disabled shape

## Status and boundary

Open local compatibility finding. Reproduced against Cal.diy v6.2.0 commit `1c193cca8682b33b9866c792186033f7ef886682` and its qualified API v2 runtime. It has not been filed upstream and is not claimed against current Cal.diy.

## Observation

Event-type output schemas describe `bookingWindow` only as an array of business-day, calendar-day, or range window objects. The runtime returns `{"disabled": true}` for event types without an active booking window. The input schema already documents that same `Disabled_2024_06_14` sentinel, but the output schema omits it.

## Impact

Strict clients reject ordinary event-type list and detail responses with the default disabled booking-window state.

## Automation policy

The validator first evaluates the unmodified pinned schema. Its known-defect projection adds `Disabled_2024_06_14` as an alternative only to a property named `bookingWindow` whose original schema is the exact array of the three window component references. F-008 is accepted only for the exact `{"disabled": true}` runtime sentinel and only when the complete repaired response validates.

## Filing policy

Phase 6 must reproduce the mismatch against current Cal.diy and search for duplicate reports before any upstream filing. Until then it remains a versioned local compatibility finding.
