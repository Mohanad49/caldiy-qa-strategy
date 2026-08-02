#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from caldiy_qa.contracts import USED_OPERATIONS, canonical_spec_path


def resolve_pointer(spec: dict[str, Any], pointer: str) -> Any:
    value: Any = spec
    for token in pointer.removeprefix("#/").split("/"):
        value = value[token.replace("~1", "/").replace("~0", "~")]
    return value


def referenced_bundle(spec: dict[str, Any], operation: Any) -> dict[str, Any]:
    references: dict[str, Any] = {}
    pending = [operation]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            reference = value.get("$ref")
            if isinstance(reference, str) and reference.startswith("#/") and reference not in references:
                resolved = resolve_pointer(spec, reference)
                references[reference] = resolved
                pending.append(resolved)
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return {"operation": operation, "references": references}


def fingerprint(spec: dict[str, Any], path: str, method: str) -> str | None:
    try:
        operation = spec["paths"][path][method]
    except (KeyError, TypeError):
        return None
    bundle = referenced_bundle(spec, operation)
    encoded = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare the public Cal.diy main contract informally")
    parser.add_argument("--current-spec", required=True, type=Path)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    args = parser.parse_args()

    pinned = json.loads(canonical_spec_path().read_text(encoding="utf-8"))
    current: dict[str, Any] | None = None
    if args.current_spec.is_file():
        loaded = json.loads(args.current_spec.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            current = loaded

    operation_results: list[dict[str, str]] = []
    for path, method in USED_OPERATIONS:
        pinned_fingerprint = fingerprint(pinned, path, method)
        current_fingerprint = fingerprint(current, path, method) if current else None
        if current_fingerprint is None:
            status = "missing"
        elif current_fingerprint == pinned_fingerprint:
            status = "unchanged"
        else:
            status = "changed"
        operation_results.append({"method": method.upper(), "path": path, "status": status})

    counts = {
        status: sum(item["status"] == status for item in operation_results)
        for status in ("unchanged", "changed", "missing")
    }
    result = {
        "schemaVersion": 1,
        "checkedAt": datetime.now(UTC).isoformat(),
        "controlledSutCommit": "1c193cca8682b33b9866c792186033f7ef886682",
        "publicMainCommit": args.current_sha,
        "informationalOnly": True,
        "counts": counts,
        "operations": operation_results,
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "### Current public Cal.diy contract advisory",
        "",
        f"Compared the controlled v6.2.0 suite surface with public `main` at `{args.current_sha}`.",
        "This is informational only: public `main` is not the controlled SUT or hosted Cal.com.",
        "",
        f"- unchanged: {counts['unchanged']}",
        f"- changed: {counts['changed']}",
        f"- missing: {counts['missing']}",
    ]
    differences = [item for item in operation_results if item["status"] != "unchanged"]
    if differences:
        lines.extend(["", "Changed or missing suite operations:"])
        lines.extend(
            f"- `{item['method']} {item['path']}` — {item['status']}" for item in differences
        )
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
