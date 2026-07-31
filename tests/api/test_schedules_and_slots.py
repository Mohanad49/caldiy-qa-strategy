from __future__ import annotations

from caldiy_qa.builders import flatten_slot_times, future_slot_query, schedule_payload
from caldiy_qa.client import ApiVersion, CalDiyClient
from caldiy_qa.factories import ResourceFactory


def test_schedule_crud(api_client: CalDiyClient, resources: ResourceFactory) -> None:
    schedule = resources.create_schedule(time_zone="Asia/Kathmandu", is_default=True)
    schedule_id = schedule["id"]

    fetched = api_client.get_schedule(schedule_id)
    assert fetched["timeZone"] == "Asia/Kathmandu"
    assert any(item["id"] == schedule_id for item in api_client.list_schedules())
    assert api_client.default_schedule()["id"] == schedule_id

    updated = api_client.update_schedule(schedule_id, {"name": "Updated isolated schedule"})
    assert updated["name"] == "Updated isolated schedule"


def test_invalid_schedule_timezone_is_rejected(api_client: CalDiyClient) -> None:
    response = api_client.request(
        "POST",
        "/v2/schedules",
        path_template="/v2/schedules",
        version=ApiVersion.SCHEDULES,
        expected_status=400,
        json_body=schedule_payload("invalid-timezone", time_zone="Mars/Olympus"),
    )

    assert response.json()["status"] == "error"


def test_slot_discovery_and_invalid_timezone(api_client: CalDiyClient, resources: ResourceFactory) -> None:
    schedule = resources.create_schedule()
    event_type = resources.create_event_type(schedule["id"])
    query = future_slot_query(event_type["id"])

    slots = flatten_slot_times(api_client.get_slots(query))
    assert slots
    assert all(slot.endswith("Z") for slot in slots[:5])

    query["timeZone"] = "Mars/Olympus"
    response = api_client.request(
        "GET",
        "/v2/slots",
        path_template="/v2/slots",
        version=ApiVersion.SLOTS,
        expected_status=400,
        params=query,
    )
    assert response.json()["status"] == "error"
