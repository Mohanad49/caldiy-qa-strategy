# CALDIY-LOCAL-003 — Guest-details text fails minimum contrast

## Status and boundary

- **Status:** Local compatibility finding; accessibility gate remains failing
- **Observed against:** Cal.diy v6.2.0, commit `1c193cca8682b33b9866c792186033f7ef886682`
- **Rule:** axe-core 4.12.1 `color-contrast`, serious
- **Surface:** Guest-details step, deterministic light color scheme

## Reproduction and evidence

Run `make test-a11y` against the complete local stack and inspect `guest-details-axe.json`. After the page reaches network idle, fonts are ready, and reduced motion is requested, the repeated final runs record five nodes with measured contrast between 2.68:1 and 4.24:1 where axe requires 4.5:1. Affected content includes the name, email and notes inputs, the add-guests text, and the consent copy.

## Impact hypothesis

Low-vision users may be unable to read required booking-form labels, inputs, supporting copy, or legal links. Axe establishes the contrast measurements; visual review under additional display and theme conditions remains necessary.

No rule or element is suppressed. The finding is limited to the historical snapshot and must be reproduced against current Cal.diy before any upstream report.
