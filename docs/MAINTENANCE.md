# Maintenance and durability

This repository is reproducible because it is pinned, not because its
dependencies never change. The controlled SUT remains Cal.diy `v6.2.0` at
`1c193cca8682b33b9866c792186033f7ef886682`; upgrading that target is a new
engagement and requires a new decision, baseline, and evidence set.

## Routine signal

The scheduled workflow exercises the controlled API twice, the timezone
matrix, performance gates, and the moving current-main advisory. A scheduled
failure is triaged into one of three buckets before changing a test:

1. controlled-snapshot product behavior;
2. test or fixture behavior;
3. infrastructure or dependency behavior.

The original failing artifact is retained. Product assertions are not retried
into green, and current-main drift never changes the controlled SUT result.

[GitHub disables scheduled workflows](https://docs.github.com/en/enterprise-cloud@latest/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
in public repositories after 60 days with no repository activity. The monthly
`Keep scheduled QA active` workflow checks the last commit and creates an empty
bot commit only after 45 quiet days. Its token has `contents: write` and no
broader permission; normal QA workflows stay read-only. This deliberately small
history cost keeps nightly evidence from silently stopping on a stable portfolio
repository.

## Dependency review

Review pins monthly and after a GitHub runner deprecation notice. Update one
toolchain at a time, retain immutable action SHAs and image digests, then run
`make validate`, clean bootstrap, API qualification, and the affected live
suite before merging.

The high-risk pins are:

- GitHub Actions and BuildKit SHAs;
- the explicit GitHub-hosted runner image (`ubuntu-24.04`, never the moving
  `ubuntu-latest` alias);
- `uv`, Python, Node, pnpm, Playwright, Cucumber, axe, and Allure;
- PostgreSQL, Redis, Mailpit, Node builder, and Cal.diy image digests;
- k6 archive versions and hashes;
- the local TestPulse adapter, exact TestPulse package commit and installation behavior;
- Python `tzdata`, which changes future transition expectations by design.

The CI `uv` pin is `0.12.1`. It replaced `0.8.17` after hosted-runner `pipx`
began requiring `uv >= 0.9.17`; a real manual run exposed that incompatibility.
Do not lower it without reproducing all five TestPulse ingestion calls.

The TestPulse adapter uses `actions/setup-python` `v7.0.0` at immutable commit
`5fda3b95a4ea91299a34e894583c3862153e4b97`. Its Node 24 action runtime replaced
the deprecated Node 20 runtime surfaced by hosted-runner annotations. Repin only
to an official immutable revision whose declared runtime is still supported.

The repository-owned TestPulse adapter installs `testpulse-core[postgres]` from
exact commit `2696d715e7b18f2ef029e291f37371d6b4bb01fb`. This closes a transitive
pinning hole in the upstream action at that commit, which installs its package
from mutable `main`. The call remains non-blocking for product confidence, but
an ingestion error must remain visible as an annotation and workflow-summary
entry. Repin TestPulse only after a manual run proves API, merged E2E, BDD, and
merged performance ingestion. The database secret is checked only for presence
and must never be echoed, copied into an artifact, or used by pull-request jobs.

## Visual baselines

Chromium screenshots are stored separately for `darwin` and `linux`; text
rasterization is platform-dependent. Desktop calendar and timeslot grid sections
are masked because their child count and geometry depend on the server's real
date. Mobile masks only the inner calendar box beneath its metadata grid area;
the auto-margin wrapper and below-the-fold slots are excluded. Runtime guards
reject masks that cover the metadata center or 75% of the viewport. The
responsive shell, metadata, time controls, borders, and branding remain compared.

Run the guarded update on the platform whose baseline is changing, inspect both
images, then rerun ordinary comparison mode at least once. A hosted-Linux actual
may be imported only after inspecting its expected/actual/diff artifact with
`make import-linux-snapshots SOURCE_DIR=... CONFIRM=caldiy-qa-strategy`; the next
ordinary Linux CI comparison must pass. A passing viewport has no failure actual,
so the guarded importer preserves that existing baseline and imports only the
failed viewport images present in the inspected artifact. Never copy a baseline
between platforms and call the result verified.

## Recovery rules

- If a registry no longer serves a pinned digest, stop and select a replacement
  from an official release; never remove digest pinning to get a build through.
- If both permitted API build heaps fail, stop. Do not substitute API v1 or
  hosted Cal.com.
- If upstream changes its seed, revalidate fixture identities and routes before
  changing smoke expectations.
- If tzdata changes, regenerate the oracle evidence and review transition
  changes rather than freezing obsolete rules.
- If an upstream issue is fixed, keep the filed report pinned to its reproduced
  commit and update only its current disposition.

## Periodic clean-room check

At least quarterly, use an amd64 machine with an empty `.env`, no project
volumes, and no local API image. Run bootstrap, repeated bootstrap, the guarded
reset, exact-source API build and qualification, all live suites, and a final
project-scoped reset. This detects dependencies accidentally satisfied only by
one workstation cache.
