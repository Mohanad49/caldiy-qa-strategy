from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from datetime import UTC, datetime, timedelta
from importlib.resources import files
from typing import Any
from zoneinfo import ZoneInfo, reset_tzpath

TARGET_ZONES = (
    "UTC",
    "America/New_York",
    "Europe/London",
    "Africa/Cairo",
    "Asia/Kolkata",
    "Asia/Kathmandu",
    "Australia/Eucla",
    "Australia/Sydney",
    "America/Phoenix",
)
TZDATA_VERSION = importlib.metadata.version("tzdata")


def main() -> None:
    _pin_tzdata_path()
    parser = argparse.ArgumentParser(prog="caldiy-timezone-oracle")
    subparsers = parser.add_subparsers(dest="command", required=True)
    matrix = subparsers.add_parser("matrix", help="emit transition and reference cases")
    matrix.add_argument("--json", action="store_true", required=True)
    convert = subparsers.add_parser("convert", help="convert stdin UTC instants through pinned tzdata")
    convert.add_argument("--json", action="store_true", required=True)
    args = parser.parse_args()

    if args.command == "matrix":
        print(json.dumps(build_matrix(), separators=(",", ":"), sort_keys=True))
    else:
        print(json.dumps(convert_request(json.load(sys.stdin)), separators=(",", ":"), sort_keys=True))


def build_matrix(now: datetime | None = None) -> dict[str, Any]:
    generated_at = (now or datetime.now(UTC)).astimezone(UTC).replace(microsecond=0)
    horizon = generated_at + timedelta(days=550)
    zones: list[dict[str, Any]] = []
    for name in TARGET_ZONES:
        transitions = find_transitions(name, generated_at - timedelta(days=2), horizon)
        next_transition = transitions[0] if transitions else None
        reference = (
            _parse_utc(next_transition["utc"])
            if next_transition is not None
            else (generated_at + timedelta(days=90)).replace(hour=12, minute=0, second=0)
        )
        window_day = reference.astimezone(ZoneInfo(name)).date()
        zones.append(
            {
                "name": name,
                "classification": _classification(name, transitions),
                "reference": convert_instant(name, reference),
                "windowStart": (window_day - timedelta(days=1)).isoformat(),
                "windowEnd": (window_day + timedelta(days=2)).isoformat(),
                "nextTransition": next_transition,
                "cases": _transition_cases(name, next_transition, reference),
            }
        )

    cairo_history = find_transitions(
        "Africa/Cairo", datetime(2023, 1, 1, tzinfo=UTC), datetime(2024, 1, 1, tzinfo=UTC)
    )
    return {
        "schemaVersion": 1,
        "generatedAt": generated_at.isoformat().replace("+00:00", "Z"),
        "tzdataVersion": TZDATA_VERSION,
        "oracle": "python-zoneinfo-with-forced-tzdata-package",
        "zones": zones,
        "pairs": {
            "opposingHemispheres": ["America/New_York", "Australia/Sydney"],
            "dstAndNonDst": ["America/New_York", "America/Phoenix"],
            "fractionalOffsets": ["Asia/Kolkata", "Asia/Kathmandu", "Australia/Eucla"],
        },
        "historicalCairo2023": cairo_history,
    }


def convert_request(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise SystemExit("convert input must be a JSON object")
    zone = payload.get("zone")
    instants = payload.get("instants")
    if not isinstance(zone, str) or zone not in TARGET_ZONES:
        raise SystemExit("convert input has an unsupported zone")
    if not isinstance(instants, list) or any(not isinstance(item, str) for item in instants):
        raise SystemExit("convert input instants must be a string array")
    return {
        "zone": zone,
        "tzdataVersion": TZDATA_VERSION,
        "instants": [convert_instant(zone, _parse_utc(item)) for item in instants],
    }


def find_transitions(zone_name: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
    zone = ZoneInfo(zone_name)
    cursor = start.astimezone(UTC).replace(minute=0, second=0, microsecond=0)
    previous_offset = cursor.astimezone(zone).utcoffset()
    transitions: list[dict[str, Any]] = []
    step = timedelta(hours=6)
    while cursor < end:
        probe = min(cursor + step, end)
        probe_offset = probe.astimezone(zone).utcoffset()
        if probe_offset != previous_offset:
            transition_utc = _bisect_transition(zone, cursor, probe, previous_offset)
            before = transition_utc - timedelta(seconds=1)
            after = transition_utc
            before_local = before.astimezone(zone)
            after_local = after.astimezone(zone)
            before_minutes = _offset_minutes(before_local)
            after_minutes = _offset_minutes(after_local)
            transitions.append(
                {
                    "utc": _utc_text(transition_utc),
                    "type": "gap" if after_minutes > before_minutes else "fold",
                    "beforeOffsetMinutes": before_minutes,
                    "afterOffsetMinutes": after_minutes,
                    "localBefore": before_local.isoformat(),
                    "localAfter": after_local.isoformat(),
                }
            )
            previous_offset = probe_offset
        cursor = probe
    return transitions


def convert_instant(zone_name: str, instant: datetime) -> dict[str, Any]:
    utc_instant = instant.astimezone(UTC).replace(microsecond=0)
    local = utc_instant.astimezone(ZoneInfo(zone_name))
    return {
        "utc": _utc_text(utc_instant),
        "local": local.isoformat(),
        "wall": local.strftime("%Y-%m-%dT%H:%M:%S"),
        "offsetMinutes": _offset_minutes(local),
        "fold": local.fold,
    }


def _pin_tzdata_path() -> None:
    package_zoneinfo = files("tzdata").joinpath("zoneinfo")
    reset_tzpath([str(package_zoneinfo)])
    ZoneInfo.clear_cache()


def _bisect_transition(
    zone: ZoneInfo, low: datetime, high: datetime, original_offset: timedelta | None
) -> datetime:
    low_epoch = int(low.timestamp())
    high_epoch = int(high.timestamp())
    while low_epoch + 1 < high_epoch:
        midpoint = (low_epoch + high_epoch) // 2
        candidate = datetime.fromtimestamp(midpoint, UTC)
        if candidate.astimezone(zone).utcoffset() == original_offset:
            low_epoch = midpoint
        else:
            high_epoch = midpoint
    return datetime.fromtimestamp(high_epoch, UTC)


def _transition_cases(
    zone_name: str, transition: dict[str, Any] | None, reference: datetime
) -> list[dict[str, Any]]:
    if transition is None:
        return [convert_instant(zone_name, reference)]
    center = _parse_utc(transition["utc"])
    return [
        convert_instant(zone_name, center + timedelta(minutes=delta))
        for delta in (-90, -30, 30, 90)
    ]


def _classification(zone_name: str, transitions: list[dict[str, Any]]) -> str:
    if transitions:
        return "dst-transition"
    offset = _offset_minutes(datetime.now(UTC).astimezone(ZoneInfo(zone_name)))
    if offset % 60:
        return "fractional-offset"
    return "fixed-offset"


def _offset_minutes(value: datetime) -> int:
    offset = value.utcoffset()
    if offset is None:
        raise AssertionError("timezone-aware datetime has no UTC offset")
    return int(offset.total_seconds() // 60)


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise SystemExit(f"instant has no UTC offset: {value}")
    return parsed.astimezone(UTC)


def _utc_text(value: datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    main()
