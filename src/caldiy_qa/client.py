from __future__ import annotations

from enum import StrEnum
from types import TracebackType
from typing import Any, TypedDict, cast

import httpx

from caldiy_qa.config import Settings
from caldiy_qa.contracts import ContractValidator, JsonObject


class ApiVersion(StrEnum):
    EVENT_TYPES = "2024-06-14"
    SCHEDULES = "2024-06-11"
    BOOKINGS = "2024-08-13"
    SLOTS = "2024-09-04"


class Identity(TypedDict, total=False):
    id: int
    email: str
    username: str
    name: str


class EventType(TypedDict, total=False):
    id: int
    title: str
    slug: str
    lengthInMinutes: int
    scheduleId: int


class Schedule(TypedDict, total=False):
    id: int
    name: str
    timeZone: str
    isDefault: bool


class Booking(TypedDict, total=False):
    id: int
    uid: str
    status: str
    start: str
    end: str


class CalDiyClient:
    def __init__(self, settings: Settings, contracts: ContractValidator) -> None:
        self.settings = settings
        self.contracts = contracts
        self._http = httpx.Client(base_url=settings.base_url, timeout=settings.timeout_seconds)

    def __enter__(self) -> CalDiyClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def request(
        self,
        method: str,
        path: str,
        *,
        path_template: str,
        version: ApiVersion | None = None,
        expected_status: int | set[int] = 200,
        authenticated: bool = True,
        api_key_override: str | None = None,
        params: dict[str, Any] | None = None,
        json_body: Any | None = None,
    ) -> httpx.Response:
        headers: dict[str, str] = {"Accept": "application/json"}
        if authenticated:
            key = api_key_override if api_key_override is not None else self.settings.api_key
            headers["Authorization"] = f"Bearer {key}"
        if version is not None:
            headers["cal-api-version"] = version.value

        response = self._http.request(method, path, headers=headers, params=params, json=json_body)
        self.contracts.validate_response(response, path_template=path_template, method=method)
        allowed = {expected_status} if isinstance(expected_status, int) else expected_status
        if response.status_code not in allowed:
            excerpt = response.text.replace("\n", " ")[:500]
            raise AssertionError(
                f"{method.upper()} {path} returned {response.status_code}; "
                f"expected {sorted(allowed)}; body={excerpt}"
            )
        return response

    def get_me(self) -> Identity:
        response = self.request("GET", "/v2/me", path_template="/v2/me")
        return cast(Identity, _data(response))

    def list_event_types(self) -> list[EventType]:
        response = self.request(
            "GET",
            "/v2/event-types",
            path_template="/v2/event-types",
            version=ApiVersion.EVENT_TYPES,
        )
        return cast(list[EventType], _data(response))

    def create_event_type(self, payload: JsonObject) -> EventType:
        response = self.request(
            "POST",
            "/v2/event-types",
            path_template="/v2/event-types",
            version=ApiVersion.EVENT_TYPES,
            expected_status=201,
            json_body=payload,
        )
        return cast(EventType, _data(response))

    def get_event_type(self, event_type_id: int) -> EventType:
        response = self.request(
            "GET",
            f"/v2/event-types/{event_type_id}",
            path_template="/v2/event-types/{eventTypeId}",
            version=ApiVersion.EVENT_TYPES,
        )
        return cast(EventType, _data(response))

    def update_event_type(self, event_type_id: int, payload: JsonObject) -> EventType:
        response = self.request(
            "PATCH",
            f"/v2/event-types/{event_type_id}",
            path_template="/v2/event-types/{eventTypeId}",
            version=ApiVersion.EVENT_TYPES,
            json_body=payload,
        )
        return cast(EventType, _data(response))

    def delete_event_type(self, event_type_id: int, *, tolerate_missing: bool = False) -> None:
        expected = {200, 404} if tolerate_missing else 200
        self.request(
            "DELETE",
            f"/v2/event-types/{event_type_id}",
            path_template="/v2/event-types/{eventTypeId}",
            version=ApiVersion.EVENT_TYPES,
            expected_status=expected,
        )

    def list_schedules(self) -> list[Schedule]:
        response = self.request(
            "GET",
            "/v2/schedules",
            path_template="/v2/schedules",
            version=ApiVersion.SCHEDULES,
        )
        return cast(list[Schedule], _data(response))

    def default_schedule(self) -> Schedule:
        response = self.request(
            "GET",
            "/v2/schedules/default",
            path_template="/v2/schedules/default",
            version=ApiVersion.SCHEDULES,
        )
        return cast(Schedule, _data(response))

    def create_schedule(self, payload: JsonObject) -> Schedule:
        response = self.request(
            "POST",
            "/v2/schedules",
            path_template="/v2/schedules",
            version=ApiVersion.SCHEDULES,
            expected_status=201,
            json_body=payload,
        )
        return cast(Schedule, _data(response))

    def get_schedule(self, schedule_id: int) -> Schedule:
        response = self.request(
            "GET",
            f"/v2/schedules/{schedule_id}",
            path_template="/v2/schedules/{scheduleId}",
            version=ApiVersion.SCHEDULES,
        )
        return cast(Schedule, _data(response))

    def update_schedule(self, schedule_id: int, payload: JsonObject) -> Schedule:
        response = self.request(
            "PATCH",
            f"/v2/schedules/{schedule_id}",
            path_template="/v2/schedules/{scheduleId}",
            version=ApiVersion.SCHEDULES,
            json_body=payload,
        )
        return cast(Schedule, _data(response))

    def delete_schedule(self, schedule_id: int, *, tolerate_missing: bool = False) -> None:
        expected = {200, 404} if tolerate_missing else 200
        self.request(
            "DELETE",
            f"/v2/schedules/{schedule_id}",
            path_template="/v2/schedules/{scheduleId}",
            version=ApiVersion.SCHEDULES,
            expected_status=expected,
        )

    def get_slots(self, params: dict[str, Any]) -> JsonObject:
        response = self.request(
            "GET",
            "/v2/slots",
            path_template="/v2/slots",
            version=ApiVersion.SLOTS,
            params=params,
        )
        return cast(JsonObject, _data(response))

    def create_booking(self, payload: JsonObject, *, expected_status: int | set[int] = 201) -> Booking:
        response = self.request(
            "POST",
            "/v2/bookings",
            path_template="/v2/bookings",
            version=ApiVersion.BOOKINGS,
            expected_status=expected_status,
            json_body=payload,
        )
        if response.status_code >= 400:
            return Booking()
        return cast(Booking, _data(response))

    def list_bookings(self) -> list[Booking]:
        response = self.request(
            "GET",
            "/v2/bookings",
            path_template="/v2/bookings",
            version=ApiVersion.BOOKINGS,
        )
        return cast(list[Booking], _data(response))

    def get_booking(self, booking_uid: str) -> Booking:
        response = self.request(
            "GET",
            f"/v2/bookings/{booking_uid}",
            path_template="/v2/bookings/{bookingUid}",
            version=ApiVersion.BOOKINGS,
        )
        return cast(Booking, _data(response))

    def reschedule_booking(self, booking_uid: str, payload: JsonObject) -> Booking:
        response = self.request(
            "POST",
            f"/v2/bookings/{booking_uid}/reschedule",
            path_template="/v2/bookings/{bookingUid}/reschedule",
            version=ApiVersion.BOOKINGS,
            expected_status=201,
            json_body=payload,
        )
        return cast(Booking, _data(response))

    def cancel_booking(self, booking_uid: str, *, tolerate_terminal: bool = False) -> None:
        expected = {200, 400, 404} if tolerate_terminal else 200
        self.request(
            "POST",
            f"/v2/bookings/{booking_uid}/cancel",
            path_template="/v2/bookings/{bookingUid}/cancel",
            version=ApiVersion.BOOKINGS,
            expected_status=expected,
            json_body={"cancellationReason": "Automated local fixture cleanup"},
        )


def _data(response: httpx.Response) -> Any:
    payload = response.json()
    if not isinstance(payload, dict) or payload.get("status") != "success" or "data" not in payload:
        raise AssertionError(
            f"Expected success envelope from {response.request.method} {response.request.url.path}"
        )
    return payload["data"]
