#!/usr/bin/env python3
"""Fail when tracked Markdown contains a broken local link."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
INLINE_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"^\s*\[[^\]]+\]:\s*(\S+)", re.MULTILINE)


def tracked_markdown() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in result.stdout.splitlines() if line]


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0]


def main() -> None:
    failures: list[str] = []
    for document in tracked_markdown():
        contents = document.read_text(encoding="utf-8")
        targets = INLINE_LINK.findall(contents) + REFERENCE_LINK.findall(contents)
        for raw_target in targets:
            target = normalize_target(raw_target)
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or (not parsed.path and parsed.fragment):
                continue
            if parsed.path.startswith("/"):
                failures.append(f"{document.relative_to(ROOT)}: absolute local link {target}")
                continue
            destination = (document.parent / unquote(parsed.path)).resolve()
            if not destination.exists():
                failures.append(
                    f"{document.relative_to(ROOT)}: missing {target}"
                )

    if failures:
        raise SystemExit("Broken Markdown links:\n" + "\n".join(sorted(failures)))
    print("Tracked Markdown links passed.")


if __name__ == "__main__":
    main()
