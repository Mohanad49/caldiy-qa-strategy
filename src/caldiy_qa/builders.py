from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from caldiy_qa.contracts import JsonObject

ALL_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass(slots=True)
class UniqueNames:
    run_id: str
    worker_id: str
    _counter: itertools.count[int] = field(default_factory=lambda: itertools.count(1))

    def next(self, purpose: str) -> str:
        raw = f"qa-{self.run_id}-{self.worker_id}-{purpose}-{next(self._counter)}".lower()
        normalized = re.sub(r"[^a-z0-9]+", "-", raw).strip("-")
        return normalized[:70]


def schedule_payload(
    name: str,
    *,
    time_zone: str = "UTC",
    is_default: bool = False,
    availability: list[JsonObject] | None = None,
) -> JsonObject:
    return {
        "name": name,
        "timeZone": time_zone,
        "isDefault": is_default,
        "availability": availability
        if availability is not None
        else [{"days": ALL_DAYS, "startTime": "09:00", "endTime": "17:00"}],
    }


def event_type_payload(name: str, schedule_id: int, *, length_minutes: int = 30) -> JsonObject:
    return {
        "title": name.replace("-", " ").title(),
        "slug": name,
        "lengthInMinutes": length_minutes,
        "scheduleId": schedule_id,
        "minimumBookingNotice": 0,
    }


def booking_payload(
    event_type_id: int,
    start: str,
    attendee_token: str,
    *,
    time_zone: str = "UTC",
) -> JsonObject:
    return {
        "eventTypeId": event_type_id,
        "start": start,
        "attendee": {
            "name": f"QA {attendee_token}",
            "email": f"qa+{attendee_token}@example.com",
            "timeZone": time_zone,
            "language": "en",
        },
        "metadata": {"qaRun": attendee_token},
    }


def future_slot_query(event_type_id: int, *, days: int = 8, time_zone: str = "UTC") -> JsonObject:
    start = (datetime.now(UTC) + timedelta(days=1)).date()
    end = start + timedelta(days=days)
    return {
        "eventTypeId": event_type_id,
        "start": start.isoformat(),
        "end": end.isoformat(),
        "timeZone": time_zone,
    }


def flatten_slot_times(slots_data: JsonObject) -> list[str]:
    times: list[str] = []
    for day_slots in slots_data.values():
        if not isinstance(day_slots, list):
            continue
        for slot in day_slots:
            if isinstance(slot, dict) and isinstance(slot.get("start"), str):
                times.append(slot["start"])
    if not times:
        raise AssertionError("Slots response data has no date-keyed start times")
    return sorted(times)
