# CALDIY-LOCAL-004 — Terms and privacy links rely on color and hover styling

## Status and boundary

- **Status:** Local compatibility finding; accessibility gate remains failing
- **Observed against:** Cal.diy v6.2.0, commit `1c193cca8682b33b9866c792186033f7ef886682`
- **Rule:** axe-core 4.12.1 `link-in-text-block`, serious
- **Surface:** Guest-details step, deterministic light color scheme

## Reproduction and evidence

Run `make test-a11y` and inspect `guest-details-axe.json`. The Terms and Privacy Policy links use `hover:underline` but have no persistent non-color distinction. In the repeated stable light-theme runs, axe measures each link at approximately 2.7:1 against the surrounding text, below the rule's 3:1 requirement.

## Impact hypothesis

Users who cannot reliably distinguish color may not recognize the two legal destinations as links before hover or focus. Keyboard and screen-reader behavior should also be checked manually before production severity is assigned.

No rule or element is suppressed. The Phase 6 audit did not exercise the
current Cal.diy UI, so this historical finding remains local and was not filed
upstream. Its disposition is recorded in `docs/defects/README.md`.
