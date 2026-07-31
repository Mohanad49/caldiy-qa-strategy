from __future__ import annotations

from caldiy_qa.client import ApiVersion, CalDiyClient
from caldiy_qa.factories import ResourceFactory


def test_event_type_crud(api_client: CalDiyClient, resources: ResourceFactory) -> None:
    schedule = resources.create_schedule()
    event_type = resources.create_event_type(schedule["id"])
    event_type_id = event_type["id"]

    fetched = api_client.get_event_type(event_type_id)
    assert fetched["slug"] == event_type["slug"]
    assert any(item["id"] == event_type_id for item in api_client.list_event_types())

    updated = api_client.update_event_type(
        event_type_id,
        {"title": "Updated by isolated API test", "lengthInMinutes": 45},
    )
    assert updated["title"] == "Updated by isolated API test"
    assert updated["lengthInMinutes"] == 45

    api_client.delete_event_type(event_type_id)


def test_event_type_missing_and_malformed_payloads(api_client: CalDiyClient) -> None:
    for payload in ({"title": "missing required fields"}, ["not", "an", "object"]):
        response = api_client.request(
            "POST",
            "/v2/event-types",
            path_template="/v2/event-types",
            version=ApiVersion.EVENT_TYPES,
            expected_status=400,
            json_body=payload,
        )
        assert response.json()["status"] == "error"


def test_event_type_not_found(api_client: CalDiyClient) -> None:
    response = api_client.request(
        "GET",
        "/v2/event-types/99999999",
        path_template="/v2/event-types/{eventTypeId}",
        version=ApiVersion.EVENT_TYPES,
        expected_status=404,
    )

    assert response.json()["error"]["code"] == "NotFoundException"
