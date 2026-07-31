from __future__ import annotations

from datetime import UTC, datetime, timedelta

from caldiy_qa.builders import ALL_DAYS, booking_payload
from caldiy_qa.cleanup import CleanupStack
from caldiy_qa.client import ApiVersion, CalDiyClient
from caldiy_qa.factories import ResourceFactory


def test_booking_lifecycle(
    api_client: CalDiyClient,
    resources: ResourceFactory,
    cleanup_stack: CleanupStack,
) -> None:
    schedule = resources.create_schedule()
    event_type = resources.create_event_type(schedule["id"])
    first_slot, second_slot = resources.first_available_slots(event_type["id"], count=2)
    booking = resources.create_booking(event_type["id"], first_slot)
    booking_uid = booking["uid"]

    fetched = api_client.get_booking(booking_uid)
    assert fetched["uid"] == booking_uid
    assert any(item["uid"] == booking_uid for item in api_client.list_bookings())

    rescheduled = api_client.reschedule_booking(
        booking_uid,
        {"start": second_slot, "reschedulingReason": "Phase 2 lifecycle coverage"},
    )
    rescheduled_uid = rescheduled["uid"]
    if rescheduled_uid != booking_uid:
        cleanup_stack.add(
            f"booking:{rescheduled_uid}",
            lambda: api_client.cancel_booking(rescheduled_uid, tolerate_terminal=True),
        )
    assert rescheduled["start"].startswith(second_slot[:16])

    api_client.cancel_booking(rescheduled_uid)
    assert api_client.get_booking(rescheduled_uid)["status"] == "cancelled"


def test_same_capacity_one_slot_allows_only_one_booking(
    api_client: CalDiyClient,
    resources: ResourceFactory,
) -> None:
    schedule = resources.create_schedule()
    event_type = resources.create_event_type(schedule["id"])
    slot = resources.first_available_slots(event_type["id"])[0]
    resources.create_booking(event_type["id"], slot, attendee_token="conflict-first")

    response = api_client.request(
        "POST",
        "/v2/bookings",
        path_template="/v2/bookings",
        version=ApiVersion.BOOKINGS,
        expected_status={400, 409},
        json_body=booking_payload(event_type["id"], slot, "conflict-second"),
    )

    assert response.json()["status"] == "error"


def test_past_and_outside_availability_bookings_are_rejected(
    api_client: CalDiyClient,
    resources: ResourceFactory,
) -> None:
    schedule = resources.create_schedule(
        availability=[{"days": ALL_DAYS, "startTime": "09:00", "endTime": "10:00"}]
    )
    event_type = resources.create_event_type(schedule["id"])
    event_type_id = event_type["id"]
    outside_start = (datetime.now(UTC) + timedelta(days=3)).replace(
        hour=18, minute=0, second=0, microsecond=0
    )

    cases = (
        booking_payload(event_type_id, "2000-01-01T09:00:00Z", "past"),
        booking_payload(
            event_type_id,
            outside_start.isoformat(),
            "outside",
        ),
    )
    for payload in cases:
        response = api_client.request(
            "POST",
            "/v2/bookings",
            path_template="/v2/bookings",
            version=ApiVersion.BOOKINGS,
            expected_status={400, 422},
            json_body=payload,
        )
        assert response.json()["status"] == "error"


def test_booking_missing_fields_invalid_timezone_and_not_found(
    api_client: CalDiyClient,
    resources: ResourceFactory,
) -> None:
    schedule = resources.create_schedule()
    event_type = resources.create_event_type(schedule["id"])
    slot = resources.first_available_slots(event_type["id"])[0]

    invalid_payloads = (
        {"eventTypeId": event_type["id"], "attendee": {"name": "Missing start", "timeZone": "UTC"}},
        booking_payload(event_type["id"], slot, "bad-zone", time_zone="Mars/Olympus"),
    )
    for payload in invalid_payloads:
        response = api_client.request(
            "POST",
            "/v2/bookings",
            path_template="/v2/bookings",
            version=ApiVersion.BOOKINGS,
            expected_status=400,
            json_body=payload,
        )
        assert response.json()["status"] == "error"

    response = api_client.request(
        "GET",
        "/v2/bookings/not-a-real-booking-uid",
        path_template="/v2/bookings/{bookingUid}",
        version=ApiVersion.BOOKINGS,
        expected_status=404,
    )
    assert response.json()["status"] == "error"
