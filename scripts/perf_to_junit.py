#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    suite = ET.Element("testsuite", name="caldiy-performance-gates")
    failures = 0
    cases = 0
    for summary_path in args.summaries:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        for metric_name, metric in sorted(summary.get("metrics", {}).items()):
            thresholds = metric.get("thresholds") if isinstance(metric, dict) else None
            if not isinstance(thresholds, dict):
                continue
            for expression, outcome in sorted(thresholds.items()):
                cases += 1
                case = ET.SubElement(
                    suite,
                    "testcase",
                    classname=f"k6.{summary_path.parent.name}",
                    name=f"{metric_name} {expression}",
                )
                values = metric.get("values", {})
                ET.SubElement(case, "system-out").text = json.dumps(values, sort_keys=True)
                if not isinstance(outcome, dict) or outcome.get("ok") is not True:
                    failures += 1
                    ET.SubElement(
                        case,
                        "failure",
                        message=f"k6 threshold failed: {metric_name} {expression}",
                    ).text = json.dumps({"outcome": outcome, "values": values}, sort_keys=True)

    if cases == 0:
        raise SystemExit("No k6 threshold outcomes were found in the supplied summaries")
    suite.set("tests", str(cases))
    suite.set("failures", str(failures))
    suite.set("errors", "0")
    suite.set("skipped", "0")
    tree = ET.ElementTree(suite)
    ET.indent(tree, space="  ")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(args.output, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
