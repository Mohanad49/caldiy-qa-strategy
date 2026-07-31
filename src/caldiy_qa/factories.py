from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from caldiy_qa.builders import (
    UniqueNames,
    booking_payload,
    event_type_payload,
    flatten_slot_times,
    future_slot_query,
    schedule_payload,
)
from caldiy_qa.cleanup import CleanupStack
from caldiy_qa.client import Booking, CalDiyClient, EventType, Schedule
from caldiy_qa.contracts import JsonObject


@dataclass(slots=True)
class ResourceFactory:
    client: CalDiyClient
    names: UniqueNames
    cleanup: CleanupStack

    def create_schedule(
        self,
        *,
        time_zone: str = "UTC",
        is_default: bool = False,
        availability: list[JsonObject] | None = None,
    ) -> Schedule:
        name = self.names.next("schedule")
        schedule = self.client.create_schedule(
            schedule_payload(
                name,
                time_zone=time_zone,
                is_default=is_default,
                availability=availability,
            )
        )
        schedule_id = _required_int(schedule, "id")
        self.cleanup.add(
            f"schedule:{schedule_id}",
            lambda: self.client.delete_schedule(schedule_id, tolerate_missing=True),
        )
        return schedule

    def create_event_type(self, schedule_id: int, *, length_minutes: int = 30) -> EventType:
        name = self.names.next("event")
        event_type = self.client.create_event_type(
            event_type_payload(name, schedule_id, length_minutes=length_minutes)
        )
        event_type_id = _required_int(event_type, "id")
        self.cleanup.add(
            f"event-type:{event_type_id}",
            lambda: self.client.delete_event_type(event_type_id, tolerate_missing=True),
        )
        return event_type

    def first_available_slots(self, event_type_id: int, *, count: int = 1) -> list[str]:
        slots_data = self.client.get_slots(future_slot_query(event_type_id))
        times = flatten_slot_times(slots_data)
        if len(times) < count:
            raise AssertionError(f"Expected at least {count} future slots for event type {event_type_id}")
        return times[:count]

    def create_booking(
        self,
        event_type_id: int,
        start: str,
        *,
        attendee_token: str | None = None,
        time_zone: str = "UTC",
    ) -> Booking:
        token = attendee_token or self.names.next("attendee")
        booking = self.client.create_booking(
            booking_payload(event_type_id, start, token, time_zone=time_zone)
        )
        booking_uid = _required_str(booking, "uid")
        self.cleanup.add(
            f"booking:{booking_uid}",
            lambda: self.client.cancel_booking(booking_uid, tolerate_terminal=True),
        )
        return booking


def _required_int(resource: Mapping[str, object], key: str) -> int:
    value = resource.get(key)
    if not isinstance(value, int):
        raise AssertionError(f"Created resource has no integer {key}")
    return value


def _required_str(resource: Mapping[str, object], key: str) -> str:
    value = resource.get(key)
    if not isinstance(value, str) or not value:
        raise AssertionError(f"Created resource has no string {key}")
    return value
