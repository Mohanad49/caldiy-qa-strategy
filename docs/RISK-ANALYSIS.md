# Timezone and DST Risk Analysis

## Purpose

Timezone correctness is the highest-priority risk in this engagement because a
booking can look valid to both participants while referring to different real
instants. The damage is not cosmetic: the parties miss the meeting, the slot may
remain unavailable, and reschedule or cancellation notices may disagree with the
product.

This document defines the failure model before implementation. It does not claim
that any listed case has been executed or that Cal.diy currently has these bugs.

## Time model and invariants

The planned tests distinguish three values that are often collapsed:

- **Instant:** the unique point on the UTC timeline stored and exchanged by the
  system.
- **Local date-time:** what a person reads, such as `09:30` on a stated date.
- **Timezone:** an IANA identifier containing historical and future offset rules,
  such as `Africa/Cairo`; it is not a fixed `UTC+02:00` label.

The core invariant is:

> Every representation of a booking must resolve to the same instant, while each
> participant sees the local date-time produced by their own IANA timezone.

Additional invariants:

1. A capacity-one instant is offered and accepted at most once.
2. A nonexistent local time is never silently normalized into a different slot.
3. An ambiguous local time identifies the intended occurrence by UTC offset or
   equivalent unambiguous data.
4. Reschedule and cancellation operate on booking identity and instant, not on a
   lossy formatted date string.
5. Confirmation UI, stored record, API response, and email agree.

## Failure catalogue

| ID | Failure mode | Observable consequence | Planned evidence |
|---|---|---|---|
| TZ-01 | Local time is stored as if it were UTC | Booking shifts by the zone offset | API value, UI labels, independent oracle |
| TZ-02 | Host and booker zones are applied in the wrong direction | Both parties see plausible but different instants | Two browser contexts plus API instant |
| TZ-03 | Offset is rounded to a whole hour | India, Nepal, or Eucla slot shifts by 15–45 minutes | Fractional-offset matrix |
| TZ-04 | Spring-forward gap is normalized silently | A nonexistent slot is bookable or moves by one hour | Gap-boundary slot enumeration |
| TZ-05 | Fall-back fold loses occurrence identity | First and second occurrence collide or display identically | Fold cases with explicit offsets |
| TZ-06 | Northern DST assumptions are reused in Sydney | Offset changes in the wrong season | Opposing-hemisphere pairing |
| TZ-07 | A non-DST booker receives host DST rules | Phoenix/UTC conversion changes at another zone's transition | Mixed-transition pairing |
| TZ-08 | Cairo uses rules from its pre-2023 no-DST period | Egyptian bookings are wrong by one hour in summer | `Africa/Cairo` transition cases |
| TZ-09 | End time is derived with the wrong offset across a transition | Duration appears shorter or longer | Boundary-spanning booking |
| TZ-10 | Availability is interpreted in the viewer's zone | Slots leak outside the host's configured working hours | Host schedule versus booker view |
| TZ-11 | Reschedule converts an already-converted local value again | Booking moves by one or two offsets | Before/after instant comparison |
| TZ-12 | Cancellation targets a formatted date instead of booking identity | Wrong folded-time occurrence is cancelled | Two same-label bookings where supported |
| TZ-13 | Email template uses server timezone | Notification disagrees with confirmation page | Mailpit body versus API and UI |
| TZ-14 | Browser, server, and oracle tzdata versions disagree | Results change after dependency or image update | Version capture and transition canary |
| TZ-15 | A process relies on host machine timezone | Local and CI runs disagree | UTC container plus multiple browser zones |
| TZ-16 | Date-only boundaries use UTC rather than user timezone | Booking limits or schedule day rolls over early/late | Midnight boundary cases |

## Zone matrix

The following zones are selected for distinct rules, not geographic coverage:

| Zone | Reason |
|---|---|
| `UTC` | Zero-offset control |
| `America/New_York` | Northern spring gap and fall fold |
| `Europe/London` | Different northern transition dates and zero/positive offsets |
| `Africa/Cairo` | DST resumed in 2023 after years without it |
| `Asia/Kolkata` | Stable half-hour offset |
| `Asia/Kathmandu` | Stable quarter-hour offset |
| `Australia/Eucla` | Uncommon `+08:45` offset |
| `Australia/Sydney` | Southern-hemisphere DST |
| `America/Phoenix` | No DST paired with zones that do transition |

The full cross-product would create noise without proportionate information.
Tests will use pairwise combinations plus targeted transition pairs. Every zone
must appear as both host and booker in at least one case.

## Deterministic test design

### What Playwright controls

A Playwright browser context can set `timezoneId`, controlling how the browser
formats dates. Playwright Clock can freeze or advance JavaScript time inside that
browser context. Those controls are necessary for repeatable UI assertions.

They do **not** freeze Cal.diy's Node process, PostgreSQL, background work, or the
container clock. Therefore “use Playwright Clock” is not a complete DST strategy.
Treating it as one would produce deterministic browser labels around a server
whose definition of “now” continues to move.

### Planned control scheme

1. Keep containers in UTC and pass IANA zone identifiers explicitly.
2. Generate transition cases from an independent Python `zoneinfo` oracle backed
   by a version-pinned `tzdata` package, not Cal.diy's JavaScript date library.
3. Select the next applicable transition within the supported booking horizon so
   cases do not expire as calendar time advances.
4. Persist explicit UTC instants for setup and compare exact instants in API
   responses before asserting localized UI text.
5. Use Playwright `timezoneId` for each participant and Clock only where the UI
   itself branches on browser time.
6. Record browser, container, Cal.diy commit, oracle tzdata version, and generated
   transition instants with the report.
7. Add fixed historical canaries, including Cairo's 2023 rule change, for logic
   that does not reject past bookings. Keep future-flow tests separate.

If API v2 cannot create the required state without consulting live server time,
Phase 2 must expose that limitation rather than bypassing validation through SQL.
The acceptable alternatives are a supported test hook upstream or dynamically
generated future transitions with the exact chosen instants recorded.

## Boundary scenarios

### Spring-forward gap

- Configure host availability spanning the local gap.
- Assert that no slot maps to the nonexistent local time.
- Book the valid instant immediately before and after the gap.
- Confirm duration and localized labels for both host and booker.

### Fall-back fold

- Enumerate both UTC instants that share the same local wall-clock label.
- Assert the product either exposes both unambiguously or applies a documented,
  consistent rule.
- Book one occurrence and verify the other is not incorrectly consumed.
- Reschedule and cancel by booking identity.

### Fractional offsets

- Pair Kolkata, Kathmandu, and Eucla with UTC and a DST zone.
- Assert minute precision in availability, booking payload, confirmation, and
  notification; a whole-hour assertion is insufficient.

### Opposing and absent DST

- Pair Sydney with New York around each zone's transition season.
- Pair Phoenix with a transitioning host and then reverse the roles.
- Assert only the zone whose rules changed receives a different offset.

### Cairo

- Include dates before and after the 2023 reintroduction as historical canaries.
- Include a future Cairo transition generated from pinned tzdata.
- Never replace `Africa/Cairo` with a fixed `UTC+02:00` expectation.

### Boundary-spanning booking

- Create an event whose elapsed duration crosses a transition.
- Assert elapsed minutes independently from the displayed start/end clock labels.
- Verify rescheduling preserves configured duration rather than a wall-clock delta.

## Oracle and assertion policy

- Compare ISO instants after normalizing to UTC; do not compare locale-formatted
  strings as the source of truth.
- Assert the IANA zone or explicit offset wherever the interface exposes it.
- Locale text assertions are secondary and scoped to the chosen locale.
- Never derive expected values with the same library and transformation used by
  the SUT; that tests the library against itself.
- A tzdata-version mismatch is reported separately from a product regression.
- Property-style checks will cover round trips: local + zone → instant → local
  must return the original unambiguous value.

## Severity guidance

| Outcome | Default severity | Reason |
|---|---|---|
| Wrong instant stored or double-booked | Critical | Core scheduling integrity is broken |
| Valid transition slot cannot be booked | High | Users lose service for a real period |
| Confirmation and notification disagree | High | Participants act on conflicting information |
| Offset/zone omitted but instant remains correct | Medium | Ambiguity and support risk without proven data loss |
| Cosmetic timezone label defect | Low | Meaning and instant remain unambiguous |

Severity is finalized from reproduced impact, not assigned mechanically from
this table.

## Exit evidence for the timezone suite — planned

The future suite is complete only when every catalogue item maps to an automated
case or a documented product limitation, each selected zone is exercised as host
and booker, transition instants and tzdata versions are retained, and failures
include API, UI, and Mailpit evidence where applicable.
