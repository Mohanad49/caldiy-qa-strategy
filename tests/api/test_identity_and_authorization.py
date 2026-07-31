from __future__ import annotations

from caldiy_qa.client import ApiVersion, CalDiyClient


def test_seed_api_key_identifies_expected_owner(api_client: CalDiyClient) -> None:
    identity = api_client.get_me()

    assert identity["email"] == "owner1-acme@example.com"
    assert identity["username"] == "owner1-acme"


def test_invalid_bearer_is_rejected(api_client: CalDiyClient) -> None:
    response = api_client.request(
        "GET",
        "/v2/me",
        path_template="/v2/me",
        expected_status=401,
        api_key_override="cal_not-a-valid-local-key",
    )

    assert response.json()["status"] == "error"


def test_other_seeded_users_resources_are_concealed(api_client: CalDiyClient) -> None:
    # Event type 3 is the deterministic official seed's pro@example.com/30min resource.
    response = api_client.request(
        "GET",
        "/v2/event-types/3",
        path_template="/v2/event-types/{eventTypeId}",
        version=ApiVersion.EVENT_TYPES,
        expected_status=404,
    )

    error = response.json()["error"]
    assert error["code"] == "NotFoundException"
    assert "not found" in error["message"].lower()

    # Schedule 1 belongs to another deterministic official seed user.
    response = api_client.request(
        "GET",
        "/v2/schedules/1",
        path_template="/v2/schedules/{scheduleId}",
        version=ApiVersion.SCHEDULES,
        expected_status=403,
    )
    assert response.json()["status"] == "error"
