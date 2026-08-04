# CALDIY-LOCAL-002 — Overlay-calendar switch has no accessible name

## Status and boundary

- **Status:** Local compatibility finding; accessibility gate remains failing
- **Observed against:** Cal.diy v6.2.0, commit `1c193cca8682b33b9866c792186033f7ef886682`
- **Rule:** axe-core 4.12.1 `button-name`, critical
- **Surfaces:** Public booking calendar and guest-details step

This finding applies only to the controlled historical snapshot. It is not a claim about hosted Cal.com or current Cal.diy, and it has not been filed upstream.

## Reproduction and evidence

1. Start the complete local stack with `make sut-api-bootstrap`.
2. Run `make test-a11y`.
3. Inspect `public-booking-axe.json` and `guest-details-axe.json` in the retained results.

On both surfaces, axe identifies the `role="switch"` element with `data-testid` beginning `overlay-calendar-switch` as having no inner text, `aria-label`, valid `aria-labelledby`, title, or associated label. The final deterministic light-theme run reports one critical node on each surface.

## Impact hypothesis

A screen-reader user can encounter an unnamed switch and cannot determine what state it controls. The automated result establishes the missing accessible name; manual assistive-technology testing is still required before assigning production severity.

No rule or element is suppressed. The Phase 6 audit did not exercise the
current Cal.diy UI, so this historical accessibility finding was not filed
upstream. Its disposition is recorded in `docs/defects/README.md`.
