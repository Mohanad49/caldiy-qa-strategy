#!/usr/bin/env python3
"""Static Phase 3 contract checks that do not require a running SUT."""

from __future__ import annotations

import json
import re
import struct
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def fail(message: str) -> None:
    raise SystemExit(f"Phase 3 validation failed: {message}")


def read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def png_dimensions(relative_path: str) -> tuple[int, int]:
    content = (REPO_ROOT / relative_path).read_bytes()
    if len(content) < 24 or content[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{relative_path} is not a valid PNG")
    return struct.unpack(">II", content[16:24])


package = json.loads(read("package.json"))
if package.get("packageManager") != "pnpm@11.17.0":
    fail("packageManager must remain pnpm@11.17.0")
if package.get("engines", {}).get("node") != ">=22 <23 || >=24 <25":
    fail("Node engine boundary no longer matches Cucumber's even-line requirement")

expected_dependencies = {
    "@axe-core/playwright": "4.12.1",
    "@cucumber/cucumber": "13.2.0",
    "@playwright/test": "1.57.0",
    "allure-playwright": "3.10.2",
    "tsx": "4.23.1",
    "typescript": "5.9.3",
}
dependencies = package.get("devDependencies", {})
for dependency, version in expected_dependencies.items():
    if dependencies.get(dependency) != version:
        fail(f"{dependency} must remain exactly pinned to {version}")

lockfile = read("pnpm-lock.yaml")
for dependency, version in expected_dependencies.items():
    pattern = rf"(?m)^\s{{6}}'?{re.escape(dependency)}'?:\n\s{{8}}specifier: {re.escape(version)}$"
    if re.search(pattern, lockfile) is None:
        fail(f"pnpm lock importer does not pin {dependency} to {version}")

feature_files = sorted((REPO_ROOT / "tests/bdd/features").glob("**/*.feature"))
if [path.relative_to(REPO_ROOT).as_posix() for path in feature_files] != [
    "tests/bdd/features/lifecycle.feature"
]:
    fail("BDD must remain one focused lifecycle feature")

scenarios = re.findall(r"(?m)^\s*Scenario:\s*(.+?)\s*$", feature_files[0].read_text(encoding="utf-8"))
if scenarios != ["Booking journey", "Rescheduling journey", "Cancellation journey"]:
    fail("BDD must contain exactly the three approved lifecycle journeys")

a11y_source = read("tests/a11y/accessibility.spec.ts")
for suppression in ("disableRules", ".exclude(", "includedImpacts"):
    if suppression in a11y_source:
        fail(f"axe suppression is forbidden: {suppression}")
for finding_id in ("CALDIY-LOCAL-002", "CALDIY-LOCAL-003", "CALDIY-LOCAL-004"):
    if finding_id not in a11y_source:
        fail(f"accessibility evidence mapping is missing {finding_id}")

expected_snapshots = {
    f"__screenshots__/{platform}/tests/visual/booking.visual.spec.ts/public-booking-1440x900.png": (
        1440,
        900,
    )
    for platform in ("darwin", "linux")
}
expected_snapshots.update(
    {
        f"__screenshots__/{platform}/tests/visual/booking.visual.spec.ts/public-booking-390x844.png": (
            390,
            844,
        )
        for platform in ("darwin", "linux")
    }
)
snapshot_root = REPO_ROOT / "__screenshots__"
actual_snapshots = {
    path.relative_to(REPO_ROOT).as_posix() for path in snapshot_root.glob("**/*.png")
}
if actual_snapshots != set(expected_snapshots):
    fail("tracked Chromium snapshot set changed without updating the Phase 3 contract")
for path, dimensions in expected_snapshots.items():
    if png_dimensions(path) != dimensions:
        fail(f"{path} dimensions are not {dimensions[0]}x{dimensions[1]}")

visual_source = read("tests/visual/booking.visual.spec.ts")
expected_masks = (
    'dynamicCalendarRegions(page, "desktop")',
    'dynamicCalendarRegions(page, "mobile")',
    "xpath=ancestor::div[contains(concat(' ', normalize-space(@class), ' '), ' mt-auto ')][1]",
    '.locator(":scope > div")',
    ':scope > [class*="[grid-area:main]"]',
    ':scope > [class*="[grid-area:timeslots]"]',
    'layout === "mobile"',
    'covers the event metadata center',
    'maskedArea / viewportArea >= 0.75',
    'prepareVisualState(page)',
    'getByTestId("time").first()',
    'transition-duration: 0s !important',
)
for mask in expected_masks:
    if mask not in visual_source:
        fail(f"expected dynamic visual mask is missing: {mask}")
visual_mask_body = (
    visual_source.split("function dynamicCalendarRegions", maxsplit=1)[1]
    .split("async function prepareVisualState", maxsplit=1)[0]
)
mobile_branch = visual_mask_body.split('layout === "mobile"', maxsplit=1)[1].split(":", maxsplit=1)[0]
if "responsiveCalendar" not in mobile_branch:
    fail("mobile visual mask must contain only the responsive calendar branch")
for unstable_child_mask in ('getByTestId("day")', 'getByTestId("time")'):
    if unstable_child_mask in visual_mask_body:
        fail(f"child-count-dependent visual mask returned: {unstable_child_mask}")

playwright_config = read("playwright.config.ts")
if "__screenshots__/{platform}/{testFilePath}/{arg}{ext}" not in playwright_config:
    fail("visual snapshots must remain platform-specific")

booking_page_source = read("tests/browser/pages/booking-page.ts")
for readiness_contract in (
    "Date.now() + 15_000",
    "status !== 404",
    "Booking route ${path} did not become ready; HTTP statuses:",
):
    if readiness_contract not in booking_page_source:
        fail(f"booking-route readiness contract is missing: {readiness_contract}")
for instant_contract in (
    'Promise<string>',
    'getAttribute("data-time")',
    'Selected time has no UTC instant',
):
    if instant_contract not in booking_page_source:
        fail(f"booking selection does not retain its UTC instant: {instant_contract}")

timezone_source = read("tests/timezones/timezones.spec.ts")
for lifecycle_contract in (
    "a New York host and Kathmandu booker keep one instant through reschedule and email",
    'hostZone = "America/New_York"',
    'bookerZone = "Asia/Kathmandu"',
    'organizerZone = "Europe/London"',
    'cross-zone-lifecycle.json',
    'wallTimeToken(requiredInstant(bookerReplacement))',
):
    if lifecycle_contract not in timezone_source:
        fail(f"cross-zone lifecycle contract is missing: {lifecycle_contract}")

update_script = read("scripts/update-snapshots.sh")
if (
    'expected="caldiy-qa-strategy"' not in update_script
    or '"${CONFIRM:-}" != "${expected}"' not in update_script
):
    fail("snapshot update confirmation guard is missing")

linux_import = read("scripts/import-linux-snapshots.sh")
for import_contract in (
    'expected="caldiy-qa-strategy"',
    '"${CONFIRM:-}" != "${expected}"',
    'public-booking-${viewport}-actual.png',
    "preserving its passing Linux baseline",
    '"${imported_count}" -eq 0',
    "scripts/validate_phase3.py",
):
    if import_contract not in linux_import:
        fail(f"Linux snapshot import contract is missing: {import_contract}")

print("Phase 3 static contracts passed.")
