#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("summaries", nargs=5, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    run_p95_ms: list[float] = []
    for summary_path in args.summaries:
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        try:
            value = float(summary["metrics"]["availability_request_duration"]["p(95)"])
        except (KeyError, TypeError, ValueError) as error:
            raise SystemExit(f"{summary_path} has no numeric availability p95: {error}") from error
        run_p95_ms.append(value)

    measured_p95_ms = max(run_p95_ms)
    threshold_ms = int(math.ceil(max(500.0, measured_p95_ms * 1.25) / 50.0) * 50)
    result = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(UTC).isoformat(),
        "policy": "max(500ms, 125% of worst run-level p95), rounded up to 50ms",
        "runP95Ms": run_p95_ms,
        "worstRunP95Ms": measured_p95_ms,
        "recommendedAvailabilityP95Ms": threshold_ms,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
