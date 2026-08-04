#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFECT_DIR = ROOT / "docs/defects"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"Phase 6 validation failed: {message}")


def main() -> None:
    register = (DEFECT_DIR / "README.md").read_text(encoding="utf-8")
    reports = sorted(DEFECT_DIR.glob("DEFECT-*.md"))
    require(len(reports) == 2, f"expected two current-main defect reports, found {len(reports)}")

    required_headings = (
        "## Status",
        "## Summary",
        "## Environment",
        "## Preconditions",
        "## Steps to reproduce",
        "## Expected result",
        "## Actual result",
        "## Severity justification",
        "## Evidence",
        "## Suspected root cause",
    )
    issue_urls = {
        "DEFECT-001": "https://github.com/calcom/cal.diy/issues/29903",
        "DEFECT-002": "https://github.com/calcom/cal.diy/issues/29904",
    }
    for report in reports:
        report_text = report.read_text(encoding="utf-8")
        report_id = report.name.split("-", 2)[:2]
        report_key = "-".join(report_id)
        require(report_key in issue_urls, f"unexpected defect report {report.name}")
        for heading in required_headings:
            require(heading in report_text, f"{report.name} is missing {heading}")
        require(issue_urls[report_key] in report_text, f"{report.name} lacks its upstream issue")
        require("Hosted Cal.com: not tested" in report_text, f"{report.name} lacks hosted-product boundary")
        require("Medium" in report_text, f"{report.name} lacks severity")
        require("Inference:" in report_text, f"{report.name} does not label root-cause inference")

    historical_ids = [f"CALDIY-LOCAL-{index:03d}" for index in range(1, 5)]
    historical_ids.extend(f"F-{index:03d}" for index in range(1, 15))
    for finding_id in historical_ids:
        require(f"| {finding_id} |" in register, f"historical disposition missing for {finding_id}")
    for issue_url in issue_urls.values():
        require(issue_url in register, f"defect register lacks {issue_url}")
    require("hosted Cal.com, which was not tested" in register, "register lacks product boundary")
    require("Schema condition remains" in register, "runtime-evidence distinction is missing")

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for issue_url in issue_urls.values():
        require(issue_url in readme, f"README lacks public defect link {issue_url}")
    require("make defects-audit" in readme, "README lacks current-main audit command")

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    require("defects-audit:" in makefile, "Makefile lacks defects-audit target")
    workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
    require("make defects-audit" in workflow, "manual/nightly CI lacks the current defect audit")
    require(
        "test-results/defects/current-main" in workflow,
        "manual/nightly CI does not retain current defect evidence",
    )
    audit = (ROOT / "scripts/current_defect_audit.py").read_text(encoding="utf-8")
    require("hostedCalComTested" in audit, "audit evidence lacks hosted-product boundary")
    require("historicalContractTriage" in audit, "audit evidence lacks historical triage")

    print("Phase 6 static contracts passed.")


if __name__ == "__main__":
    main()
