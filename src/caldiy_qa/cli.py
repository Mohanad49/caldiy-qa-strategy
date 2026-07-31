from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from caldiy_qa.builders import UniqueNames
from caldiy_qa.cleanup import CleanupStack
from caldiy_qa.client import CalDiyClient
from caldiy_qa.config import Settings
from caldiy_qa.contracts import ContractValidator
from caldiy_qa.factories import ResourceFactory


def main() -> None:
    parser = argparse.ArgumentParser(prog="caldiy-fixtures")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="create an isolated schedule and event type")
    create_parser.add_argument("--json", action="store_true", required=True, help="emit a JSON manifest")
    create_parser.add_argument("--time-zone", default="UTC")
    create_parser.add_argument("--start-time", default="09:00")
    create_parser.add_argument("--end-time", default="17:00")
    create_parser.add_argument("--length-minutes", type=int, default=30)

    destroy_parser = subparsers.add_parser("destroy", help="destroy resources from a JSON manifest")
    destroy_parser.add_argument("--json", action="store_true", required=True, help="emit a JSON result")
    destroy_parser.add_argument("--manifest", type=Path, help="manifest path; defaults to stdin")

    args = parser.parse_args()
    if args.command == "create":
        _create(
            time_zone=args.time_zone,
            start_time=args.start_time,
            end_time=args.end_time,
            length_minutes=args.length_minutes,
        )
    else:
        _destroy(manifest_path=args.manifest)


def _create(*, time_zone: str, start_time: str, end_time: str, length_minutes: int) -> None:
    if length_minutes < 5 or length_minutes > 720:
        raise SystemExit("length-minutes must be between 5 and 720")
    run_id = os.getenv("QA_RUN_ID") or f"{datetime.now(UTC):%Y%m%d%H%M%S}-{uuid.uuid4().hex[:8]}"
    worker_id = os.getenv("PYTEST_XDIST_WORKER", "cli")
    contracts = ContractValidator.load()
    contracts.validate_documents()
    cleanup = CleanupStack()
    with CalDiyClient(Settings.from_env(), contracts) as client:
        try:
            factory = ResourceFactory(
                client=client,
                names=UniqueNames(run_id=run_id, worker_id=worker_id),
                cleanup=cleanup,
            )
            schedule = factory.create_schedule(
                time_zone=time_zone,
                availability=[
                    {
                        "days": [
                            "Monday",
                            "Tuesday",
                            "Wednesday",
                            "Thursday",
                            "Friday",
                            "Saturday",
                            "Sunday",
                        ],
                        "startTime": start_time,
                        "endTime": end_time,
                    }
                ],
            )
            schedule_id = _manifest_id(schedule, "schedule")
            event_type = factory.create_event_type(schedule_id, length_minutes=length_minutes)
            event_type_id = _manifest_id(event_type, "event type")
            event_type_slug = _manifest_string(event_type, "slug", "event type")
            event_type_title = _manifest_string(event_type, "title", "event type")
            manifest = {
                "schemaVersion": 1,
                "runId": run_id,
                "workerId": worker_id,
                "resources": {
                    "eventTypeIds": [event_type_id],
                    "scheduleIds": [schedule_id],
                    "eventTypes": [
                        {
                            "id": event_type_id,
                            "slug": event_type_slug,
                            "title": event_type_title,
                            "username": "owner1-acme",
                            "bookingPath": f"/owner1-acme/{event_type_slug}",
                        }
                    ],
                    "schedules": [{"id": schedule_id, "timeZone": time_zone}],
                },
            }
            print(json.dumps(manifest, separators=(",", ":"), sort_keys=True))
        except Exception:
            failures = cleanup.close()
            for failure in failures:
                print(f"cleanup failure for {failure.label}: {failure.error}", file=sys.stderr)
            raise


def _destroy(*, manifest_path: Path | None) -> None:
    raw = manifest_path.read_text(encoding="utf-8") if manifest_path else sys.stdin.read()
    if not raw.strip():
        raise SystemExit("destroy requires a JSON manifest through --manifest or stdin")
    manifest = json.loads(raw)
    if not isinstance(manifest, dict) or manifest.get("schemaVersion") != 1:
        raise SystemExit("unsupported or malformed fixture manifest")
    resources = manifest.get("resources")
    if not isinstance(resources, dict):
        raise SystemExit("fixture manifest has no resources object")

    errors: list[dict[str, Any]] = []
    contracts = ContractValidator.load()
    with CalDiyClient(Settings.from_env(), contracts) as client:
        for event_type_id in reversed(_integer_ids(resources.get("eventTypeIds"))):
            try:
                client.delete_event_type(event_type_id, tolerate_missing=True)
            except Exception as error:
                errors.append({"resource": f"event-type:{event_type_id}", "error": str(error)})
        for schedule_id in reversed(_integer_ids(resources.get("scheduleIds"))):
            try:
                client.delete_schedule(schedule_id, tolerate_missing=True)
            except Exception as error:
                errors.append({"resource": f"schedule:{schedule_id}", "error": str(error)})

    result = {"status": "destroyed" if not errors else "cleanup_failed", "errors": errors}
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    if errors:
        raise SystemExit(1)


def _manifest_id(resource: Mapping[str, object], label: str) -> int:
    resource_id = resource.get("id")
    if not isinstance(resource_id, int):
        raise AssertionError(f"created {label} has no integer id")
    return resource_id


def _manifest_string(resource: Mapping[str, object], key: str, label: str) -> str:
    value = resource.get(key)
    if not isinstance(value, str) or not value:
        raise AssertionError(f"created {label} has no string {key}")
    return value


def _integer_ids(value: object) -> list[int]:
    if not isinstance(value, list) or any(not isinstance(item, int) for item in value):
        raise SystemExit("fixture manifest resource IDs must be integer arrays")
    return value


if __name__ == "__main__":
    main()
