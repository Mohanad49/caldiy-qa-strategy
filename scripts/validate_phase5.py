#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
QUALITY = ROOT / ".github/workflows/validate.yml"
PAGES = ROOT / ".github/workflows/pages.yml"
ACTION = ROOT / ".github/actions/api-image/action.yml"


def read(path: Path | str) -> str:
    target = ROOT / path if isinstance(path, str) else path
    return target.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Phase 5 validation failed: {message}")


def validate_action_pins(text: str, label: str) -> None:
    for reference in re.findall(r"^\s*uses:\s*([^\s#]+)", text, flags=re.MULTILINE):
        if reference.startswith("./"):
            continue
        require(
            re.fullmatch(r"[^@]+@[0-9a-f]{40}", reference) is not None,
            f"{label} has a mutable action reference: {reference}",
        )


def main() -> None:
    required = (
        ".github/actions/api-image/action.yml",
        ".github/workflows/validate.yml",
        ".github/workflows/pages.yml",
        "docs/PHASE-5-CI.md",
        "playwright.merge.config.ts",
        "scripts/ci-api-build.sh",
        "scripts/ci-free-disk.sh",
        "scripts/ci-sut-bootstrap.sh",
        "scripts/current-upstream-advisory.sh",
        "scripts/current_upstream_contract_advisory.py",
        "scripts/generate-allure-report.sh",
        "scripts/merge_junit.py",
    )
    for relative in required:
        path = ROOT / relative
        require(path.is_file() and path.stat().st_size > 0, f"missing or empty {relative}")

    for path in (QUALITY, PAGES, ACTION):
        parsed = yaml.safe_load(read(path))
        require(isinstance(parsed, dict), f"{path.name} is not a YAML mapping")

    quality = read(QUALITY)
    pages = read(PAGES)
    action = read(ACTION)
    validate_action_pins(quality, "quality workflow")
    validate_action_pins(pages, "Pages workflow")
    validate_action_pins(action, "API composite action")
    runtime_helper = (
        "crazy-max/ghaction-github-runtime@"
        "04d248b84655b509d8c44dc1d6f990c879747487"
    )
    require(runtime_helper in action, "GitHub cache runtime helper pin changed or is missing")

    for trigger in ("pull_request:", "push:", "schedule:", "workflow_dispatch:"):
        require(trigger in quality, f"tiered workflow trigger missing: {trigger}")
    for job in (
        "validate:",
        "prewarm_api:",
        "api:",
        "api_repeat:",
        "e2e_shard:",
        "merge_e2e:",
        "browser_quality:",
        "timezone:",
        "performance:",
        "upstream_advisory:",
        "allure:",
    ):
        require(f"  {job}" in quality, f"tiered workflow job missing: {job}")

    require("shard: [1, 2, 3, 4]" in quality, "Playwright must use exactly four shards")
    require("--reporter=blob" in quality, "shards must emit blob reports only")
    require(
        quality.index("playwright merge-reports") < quality.index("suite: caldiy-e2e"),
        "Playwright ingestion must occur only after blob merging",
    )
    require("test \"$(find all-blob-reports" in quality, "merge job does not require four blobs")
    require("playwright.json" in quality and "junit.xml" in quality, "merged report outputs are incomplete")

    suites = re.findall(r"^\s*suite:\s*(caldiy-[a-z0-9-]+)\s*$", quality, flags=re.MULTILINE)
    require(
        set(suites)
        == {"caldiy-api-v2", "caldiy-e2e", "caldiy-bdd", "caldiy-performance-gates"},
        f"unexpected TestPulse suite set: {sorted(set(suites))}",
    )
    require(suites.count("caldiy-api-v2") == 2, "nightly must produce two isolated API ingestions")
    testpulse_sha = "Mohanad49/testpulse@2696d715e7b18f2ef029e291f37371d6b4bb01fb"
    require(quality.count(testpulse_sha) == 5, "TestPulse action count or pin changed")
    for position in [match.start() for match in re.finditer(re.escape(testpulse_sha), quality)]:
        prefix = quality[max(0, position - 450) : position]
        require("continue-on-error: true" in prefix, "TestPulse ingestion is not non-blocking")
    require("pull_request" in quality, "pull-request tier is missing")
    require("if: github.event_name != 'pull_request'" in quality, "main-only ingestion boundary is missing")
    require("set -x" not in quality, "workflow enables shell tracing around secrets")
    require(
        not re.search(r"echo[^\n]*\$\{?TESTPULSE_DATABASE_URL", quality),
        "workflow prints the TestPulse secret value",
    )

    require("retention-days: 14" in quality, "failure evidence retention is not 14 days")
    require("retention-days: 30" in quality, "report retention is not 30 days")
    require("allure-report" in quality, "merged Allure artifact is missing")
    require('"allure-commandline": "2.43.0"' in read("package.json"), "Allure CLI pin changed")

    api_build = read("scripts/ci-api-build.sh")
    disk_cleanup = read("scripts/ci-free-disk.sh")
    for contract in (
        "--cache-from \"type=gha,scope=${cache_scope}\"",
        "outputs+=(--cache-to \"type=gha,scope=${cache_scope},mode=max\")",
        "outputs+=(--load)",
        "accepted_heap=8192",
        "accepted_heap=6144",
        'redistributable}" == "false"',
        'ACTIONS_RESULTS_URL:-',
        'ACTIONS_RUNTIME_TOKEN:-',
    ):
        require(contract in api_build, f"CI API build contract missing: {contract}")
    require(
        'android_root="/usr/local/lib/android"' in disk_cleanup,
        "CI disk cleanup target changed",
    )
    require(
        '"${RUNNER_ENVIRONMENT:-}" == "github-hosted"' in disk_cleanup
        and '"${RUNNER_OS:-}" == "Linux"' in disk_cleanup,
        "CI disk cleanup lost its ephemeral hosted-Linux guard",
    )
    require(
        "./scripts/ci-free-disk.sh" in action
        and action.index("./scripts/ci-free-disk.sh") < action.index("./scripts/ci-api-build.sh"),
        "hosted-runner disk cleanup must run before the API build",
    )
    require(
        'load_image: "false"' in quality and 'write_cache: "true"' in quality,
        "prewarm job must write cache layers without loading the runtime image",
    )
    require(
        "CI_API_BUILD_LOAD" in action and "CI_API_CACHE_WRITE" in action,
        "API composite action does not expose the cache/load boundary",
    )
    combined = "\n".join((quality, action, api_build))
    for forbidden in ("docker push", "push: true", "ghcr.io", "docker.io/"):
        require(forbidden not in combined, f"CI attempts to distribute API image via {forbidden}")

    require("make contracts-verify" in quality, "pull-request live contract verification is missing")
    require("make test-api" in quality, "complete API suite is missing from main/nightly")
    for browser_gate in ("make test-bdd", "make test-a11y", "./scripts/browser-test.sh visual"):
        require(browser_gate in quality, f"main browser gate missing: {browser_gate}")
    for nightly_gate in ("make test-timezones", "make test-perf", "make test-contention"):
        require(nightly_gate in quality, f"nightly gate missing: {nightly_gate}")
    require("current-upstream-advisory.sh" in quality, "current-upstream advisory is missing")
    require("continue-on-error: true" in quality, "informational/non-blocking steps are missing")

    merge_script = read("scripts/merge_junit.py")
    require("Duplicate JUnit natural key" in merge_script, "JUnit merger does not reject duplicates")
    require("caldiy-performance-gates" in quality, "performance JUnit suite name changed")

    require("workflow_dispatch:" in pages, "Pages preparation is not manually triggered")
    require("push:" not in pages and "workflow_run:" not in pages, "Pages can publish automatically")
    require(
        "if: vars.ENABLE_ALLURE_PAGES == 'true'" in pages,
        "Pages publication lacks explicit public-release enablement",
    )

    package = json.loads(read("package.json"))
    require(
        package.get("devDependencies", {}).get("allure-commandline") == "2.43.0",
        "Allure CLI is not exactly pinned",
    )
    require(
        "playwright.merge.config.ts" in json.loads(read("tsconfig.json"))["include"],
        "Playwright merge config is outside TypeScript validation",
    )

    evidence = " ".join(read("docs/PHASE-5-CI.md").lower().split())
    for statement in (
        "not a production slo",
        "no ci badge",
        "workflow has not yet run",
        "never targets hosted cal.com",
        "enable_allure_pages=true",
    ):
        require(statement in evidence, f"Phase 5 evidence boundary missing: {statement}")

    print("Phase 5 static contracts passed.")


if __name__ == "__main__":
    main()
