#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import xml.etree.ElementTree as ET
from pathlib import Path


def suites(root: ET.Element) -> list[ET.Element]:
    if root.tag == "testsuite":
        return [root]
    if root.tag == "testsuites":
        return list(root.findall("testsuite"))
    raise SystemExit(f"Unsupported JUnit root element: {root.tag}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge JUnit without duplicate test identities")
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--suite", required=True)
    args = parser.parse_args()

    merged = ET.Element("testsuite", name=args.suite)
    identities: set[tuple[str, str]] = set()
    counters = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    duration = 0.0

    for input_path in args.inputs:
        for source_suite in suites(ET.parse(input_path).getroot()):
            for case in source_suite.findall("testcase"):
                identity = (case.get("classname", ""), case.get("name", ""))
                if identity in identities:
                    raise SystemExit(f"Duplicate JUnit natural key {identity!r} from {input_path}")
                identities.add(identity)
                merged.append(copy.deepcopy(case))
                counters["tests"] += 1
                counters["failures"] += int(case.find("failure") is not None)
                counters["errors"] += int(case.find("error") is not None)
                counters["skipped"] += int(case.find("skipped") is not None)
                try:
                    duration += float(case.get("time", "0"))
                except ValueError:
                    pass

    if counters["tests"] == 0:
        raise SystemExit("No JUnit test cases were found")
    for key, value in counters.items():
        merged.set(key, str(value))
    merged.set("time", f"{duration:.6f}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(merged)
    ET.indent(tree, space="  ")
    tree.write(args.output, encoding="utf-8", xml_declaration=True)


if __name__ == "__main__":
    main()
