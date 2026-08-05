# Public release checklist

Public visibility does not broaden the test boundary: this remains evidence for
Cal.diy `v6.2.0`, not current hosted Cal.com.

## Before changing visibility

- Confirm `main` is pushed and the worktree is clean.
- Run `make validate` and inspect the latest live workflow artifacts.
- Confirm `TESTPULSE_DATABASE_URL` exists by name only; never display its value.
- Confirm `ENABLE_ALLURE_PAGES` is absent while the repository is private.
- Confirm no API v2 image or image archive exists in Packages or workflow
  artifacts.
- Confirm the monthly keepalive workflow is enabled so GitHub does not disable
  scheduled QA after a long period without public-repository activity.
- Review `README.md`, `DECISIONS.md`, both public defect links, and the explicit
  historical/current/hosted product boundaries.

The quality workflow may be red for the unsuppressed accessibility findings.
That is an evidence-backed product result, not permission to add retries,
waivers, or a green badge. The README must identify the exact failing gate.

## After changing visibility to public

1. Recheck repository visibility and secret names. GitHub does not expose secret
   values when a repository becomes public, but the workflow permissions and
   pull-request ingestion boundary still require review.
2. In repository settings, select GitHub Actions as the Pages source.
3. Add repository variable `ENABLE_ALLURE_PAGES=true`.
4. Manually run **Publish Allure to Pages** with a Cal.diy QA run ID that
   contains the `allure-report` artifact.
5. Verify the deployed URL, then add it to the repository homepage and README.
6. Add a CI badge only after a real quality workflow has completed successfully;
   never badge a partial job or hide a failing product gate.

The repository currently grants no reuse license. Public visibility permits
inspection but is not an open-source license. Choose and add a license only as
an explicit owner decision.
