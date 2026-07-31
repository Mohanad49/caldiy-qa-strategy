#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    compose = str(REPO_ROOT / "scripts/compose.sh")
    container_ids = command(compose, "--profile", "api", "ps", "-q").splitlines()
    containers: list[dict[str, str]] = []
    if container_ids:
        raw_stats = command(
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{json .}}",
            *container_ids,
        )
        containers = [json.loads(line) for line in raw_stats.splitlines() if line]

    result = {
        "schemaVersion": 1,
        "capturedAt": datetime.now(UTC).isoformat(),
        "sut": {
            "repository": "calcom/cal.diy",
            "tag": "v6.2.0",
            "commit": "1c193cca8682b33b9866c792186033f7ef886682",
        },
        "testRepositoryCommit": command("git", "rev-parse", "HEAD"),
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
        },
        "docker": {
            "serverVersion": command("docker", "version", "--format", "{{.Server.Version}}"),
            "memoryBytes": int(command("docker", "info", "--format", "{{.MemTotal}}")),
            "containers": containers,
        },
        "k6Version": command(str(REPO_ROOT / "scripts/k6.sh"), "version").splitlines()[0],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
