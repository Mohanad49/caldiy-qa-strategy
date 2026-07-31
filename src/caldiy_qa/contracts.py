from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, cast

import httpx
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from openapi_schema_validator import OAS30Validator
from openapi_spec_validator import validate
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT4

JsonObject = dict[str, Any]
EXPECTED_OPENAPI_SHA256: Final = "e9e662d1183733ee57da8ac02a60891c67e021df47c30b4d6fd29bdad60a0cfb"
USED_OPERATIONS: Final[tuple[tuple[str, str], ...]] = (
    ("/v2/me", "get"),
    ("/v2/event-types", "get"),
    ("/v2/event-types", "post"),
    ("/v2/event-types/{eventTypeId}", "get"),
    ("/v2/event-types/{eventTypeId}", "patch"),
    ("/v2/event-types/{eventTypeId}", "delete"),
    ("/v2/schedules", "get"),
    ("/v2/schedules", "post"),
    ("/v2/schedules/default", "get"),
    ("/v2/schedules/{scheduleId}", "get"),
    ("/v2/schedules/{scheduleId}", "patch"),
    ("/v2/schedules/{scheduleId}", "delete"),
    ("/v2/slots", "get"),
    ("/v2/bookings", "get"),
    ("/v2/bookings", "post"),
    ("/v2/bookings/{bookingUid}", "get"),
    ("/v2/bookings/{bookingUid}/reschedule", "post"),
    ("/v2/bookings/{bookingUid}/cancel", "post"),
)


class ContractOmissionWarning(UserWarning):
    """The upstream operation has no schema for an observed error status."""


class KnownContractDeviationWarning(UserWarning):
    """A response hit an exact, evidence-backed defect in the pinned schema."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def canonical_spec_path() -> Path:
    return repository_root() / "contracts" / "api-v2" / "openapi-v6.2.0.json"


def common_error_schema_path() -> Path:
    return repository_root() / "contracts" / "api-v2" / "common-error-envelope.schema.json"


@dataclass(slots=True)
class ContractValidator:
    spec: JsonObject
    error_schema: JsonObject
    omissions: set[tuple[str, str, int]] = field(default_factory=set)
    schema_deviations: set[tuple[str, str, str]] = field(default_factory=set)
    full_spec_validation_error: str | None = None
    suite_spec_validation_error: str | None = None

    @classmethod
    def load(cls) -> ContractValidator:
        spec = _load_json(canonical_spec_path())
        error_schema = _load_json(common_error_schema_path())
        return cls(spec=spec, error_schema=error_schema)

    def validate_documents(self) -> None:
        try:
            validate(self.spec)
        except OpenAPIValidationError as error:
            self.full_spec_validation_error = f"{type(error).__name__}: {error}"
        suite_spec = self._suite_surface_spec()
        try:
            validate(suite_spec)
        except OpenAPIValidationError as error:
            self.suite_spec_validation_error = f"{type(error).__name__}: {error}"
        validate(_without_schema_annotations(suite_spec))
        Draft202012Validator.check_schema(self.error_schema)

    def _suite_surface_spec(self) -> JsonObject:
        reduced = {key: copy.deepcopy(value) for key, value in self.spec.items() if key != "paths"}
        reduced_paths: JsonObject = {}
        operations_by_path: dict[str, set[str]] = {}
        for path, method in USED_OPERATIONS:
            operations_by_path.setdefault(path, set()).add(method)
        http_methods = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
        for path, methods in operations_by_path.items():
            original_item = self.spec["paths"][path]
            reduced_paths[path] = {
                key: copy.deepcopy(value)
                for key, value in original_item.items()
                if key not in http_methods or key in methods
            }
        reduced["paths"] = reduced_paths
        return reduced

    def validate_response(
        self,
        response: httpx.Response,
        *,
        path_template: str,
        method: str,
    ) -> None:
        if not response.content:
            return
        try:
            payload = response.json()
        except ValueError as error:
            raise AssertionError(
                f"{method.upper()} {path_template} returned non-JSON status {response.status_code}"
            ) from error

        operation = self._operation(path_template, method)
        responses = operation.get("responses", {})
        response_contract = responses.get(str(response.status_code), responses.get("default"))
        schema: JsonObject | None = None
        if isinstance(response_contract, dict):
            content = response_contract.get("content", {})
            json_content = content.get("application/json", {}) if isinstance(content, dict) else {}
            candidate = json_content.get("schema") if isinstance(json_content, dict) else None
            if isinstance(candidate, dict):
                schema = candidate

        if schema is None:
            if response.status_code < 400:
                raise AssertionError(
                    f"Upstream OpenAPI has no JSON schema for successful {method.upper()} "
                    f"{path_template} status {response.status_code}"
                )
            omission = (path_template, method.lower(), response.status_code)
            self.omissions.add(omission)
            warnings.warn(
                f"Upstream OpenAPI omits {response.status_code} for {method.upper()} {path_template}; "
                "validated against the committed common error envelope",
                ContractOmissionWarning,
                stacklevel=3,
            )
            self._validate_json(self.error_schema, payload, use_openapi_root=False, label=str(omission))
            return

        self._validate_json(
            schema,
            payload,
            use_openapi_root=True,
            label=f"{method.upper()} {path_template} {response.status_code}",
        )

    def _operation(self, path_template: str, method: str) -> JsonObject:
        paths = self.spec.get("paths")
        if not isinstance(paths, dict) or path_template not in paths:
            raise AssertionError(f"Operation path is absent from pinned OpenAPI: {path_template}")
        path_item = paths[path_template]
        operation = path_item.get(method.lower()) if isinstance(path_item, dict) else None
        if not isinstance(operation, dict):
            raise AssertionError(f"Operation is absent from pinned OpenAPI: {method.upper()} {path_template}")
        return operation

    def _validate_json(
        self,
        schema: JsonObject,
        instance: Any,
        *,
        use_openapi_root: bool,
        label: str,
    ) -> None:
        try:
            if use_openapi_root:
                registry = Registry().with_resource(
                    "urn:caldiy:openapi",
                    Resource.from_contents(self.spec, default_specification=DRAFT4),
                )
                validator = OAS30Validator(
                    _absolute_openapi_refs(schema),
                    registry=registry,
                    format_checker=FormatChecker(),
                )
                unknown_errors: list[ValidationError] = []
                for error in validator.iter_errors(instance):
                    finding_id = _known_deviation_finding(error)
                    if finding_id is None:
                        unknown_errors.append(error)
                        continue
                    location = _error_location(error)
                    deviation = (finding_id, label, location)
                    if deviation not in self.schema_deviations:
                        self.schema_deviations.add(deviation)
                        warnings.warn(
                            f"{finding_id} known pinned-schema deviation for {label} at {location}: "
                            f"{_error_summary(error)}",
                            KnownContractDeviationWarning,
                            stacklevel=4,
                        )
                if unknown_errors:
                    repaired_spec = _with_known_schema_repairs(self.spec)
                    repaired_registry = Registry().with_resource(
                        "urn:caldiy:openapi",
                        Resource.from_contents(repaired_spec, default_specification=DRAFT4),
                    )
                    repaired_validator = OAS30Validator(
                        _with_known_schema_repairs(_absolute_openapi_refs(schema)),
                        registry=repaired_registry,
                        format_checker=FormatChecker(),
                    )
                    repaired_errors = list(repaired_validator.iter_errors(instance))
                    if repaired_errors:
                        raise repaired_errors[0]
                    for error in unknown_errors:
                        finding_ids = _known_repairs_explaining_parent(error)
                        if not finding_ids:
                            raise error
                        location = _error_location(error)
                        for finding_id in finding_ids:
                            deviation = (finding_id, label, location)
                            if deviation not in self.schema_deviations:
                                self.schema_deviations.add(deviation)
                                warnings.warn(
                                    f"{finding_id} known pinned-schema deviation for {label} at {location}: "
                                    f"{_error_summary(error)}",
                                    KnownContractDeviationWarning,
                                    stacklevel=4,
                                )
            else:
                Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)
        except ValidationError as error:
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            raise AssertionError(f"Contract mismatch for {label} at {location}: {error.message}") from error


def verify_contracts(runtime_url: str) -> None:
    spec_path = canonical_spec_path()
    digest = hashlib.sha256(spec_path.read_bytes()).hexdigest()
    if digest != EXPECTED_OPENAPI_SHA256:
        raise SystemExit(f"Pinned OpenAPI hash is {digest}; expected {EXPECTED_OPENAPI_SHA256}")

    validator = ContractValidator.load()
    validator.validate_documents()
    runtime_response = httpx.get(f"{runtime_url.rstrip('/')}/docs-json", timeout=60.0)
    runtime_response.raise_for_status()
    runtime_spec = runtime_response.json()
    mismatches: list[str] = []
    for path, method in USED_OPERATIONS:
        try:
            pinned_operation = validator.spec["paths"][path][method]
            runtime_operation = runtime_spec["paths"][path][method]
        except (KeyError, TypeError):
            mismatches.append(f"missing {method.upper()} {path}")
            continue
        if pinned_operation != runtime_operation:
            mismatches.append(f"changed {method.upper()} {path}")
    if mismatches:
        raise SystemExit("Runtime OpenAPI differs for suite operations: " + ", ".join(mismatches))

    print(
        f"Suite contract verification passed: SHA-256 {digest}; "
        f"{len(USED_OPERATIONS)} runtime operations match the v6.2.0 snapshot."
    )
    if validator.full_spec_validation_error:
        print(
            "Known full-document validation failure outside the suite surface: "
            f"{validator.full_spec_validation_error}"
        )
    if validator.suite_spec_validation_error:
        print(
            "Known suite-document annotation failure: "
            f"{validator.suite_spec_validation_error}"
        )


def _load_json(path: Path) -> JsonObject:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise TypeError(f"Expected a JSON object in {path}")
    return loaded


def _absolute_openapi_refs(value: Any) -> Any:
    if isinstance(value, dict):
        rewritten: JsonObject = {}
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str) and item.startswith("#"):
                rewritten[key] = f"urn:caldiy:openapi{item}"
            else:
                rewritten[key] = _absolute_openapi_refs(item)
        return rewritten
    if isinstance(value, list):
        return [_absolute_openapi_refs(item) for item in value]
    return value


def _without_schema_annotations(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _without_schema_annotations(item)
            for key, item in value.items()
            if key not in {"example", "examples", "default"}
        }
    if isinstance(value, list):
        return [_without_schema_annotations(item) for item in value]
    return value


def _known_deviation_finding(error: ValidationError) -> str | None:
    path = list(error.absolute_path)
    leaf = path[-1] if path else None
    if (
        leaf == "isDefault"
        and error.validator == "type"
        and error.validator_value == "object"
        and isinstance(error.instance, bool)
    ):
        return "F-002"
    schema = error.schema
    if (
        leaf == "days"
        and error.validator == "enum"
        and isinstance(error.instance, list)
        and isinstance(schema, dict)
        and schema.get("type") == "array"
        and isinstance(schema.get("enum"), list)
        and all(isinstance(item, str) for item in schema["enum"])
    ):
        return "F-003"
    if (
        leaf in {"startTime", "endTime"}
        and error.validator == "pattern"
        and error.validator_value == "TIME_FORMAT_HH_MM"
        and isinstance(error.instance, str)
        and re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", error.instance)
    ):
        return "F-004"
    if (
        leaf in {"rescheduledByEmail", "rating"}
        and error.validator == "type"
        and error.instance is None
    ):
        return "F-012"
    if (
        leaf in {"description", "meetingUrl", "location"}
        and error.validator == "type"
        and error.instance is None
    ):
        return "F-013"
    if (
        leaf in {"eventTypeId", "eventType"}
        and error.validator == "type"
        and error.instance is None
    ):
        return "F-014"
    return None


def _known_repairs_explaining_parent(error: ValidationError) -> set[str]:
    findings: set[str] = set()
    for child in error.context:
        direct_finding = _known_deviation_finding(child)
        if direct_finding is not None:
            findings.add(direct_finding)
        findings.update(_known_repairs_explaining_parent(child))
    if (
        error.validator in {"oneOf", "anyOf"}
        and isinstance(error.instance, dict)
        and isinstance(error.instance.get("isDefault"), bool)
    ):
        findings.add("F-002")
    union = error.schema.get("oneOf") if isinstance(error.schema, dict) else None
    if error.validator == "oneOf" and _is_default_booking_field_union(union):
        findings.add("F-005")
    path = list(error.absolute_path)
    if path and path[-1] == "recurrence" and error.instance is None:
        findings.add("F-006")
    if (
        path
        and path[-1] == "forwardParamsSuccessRedirect"
        and isinstance(error.instance, bool)
        and error.validator == "type"
        and error.validator_value == "object"
    ):
        findings.add("F-007")
    if (
        path
        and path[-1] == "bookingWindow"
        and error.validator == "type"
        and error.validator_value == "array"
        and error.instance == {"disabled": True}
    ):
        findings.add("F-008")
    if (
        path
        and path[-1] == "seats"
        and error.validator == "required"
        and error.instance == {"disabled": True}
    ):
        findings.add("F-009")
    if (
        len(path) >= 2
        and path[-2] == "users"
        and error.validator == "type"
        and error.validator_value == "string"
        and isinstance(error.instance, dict)
    ):
        findings.add("F-010")
    if (
        error.validator == "oneOf"
        and _is_broken_slots_response_union(error.schema)
        and isinstance(error.instance, dict)
        and error.instance.get("status") == "success"
        and isinstance(error.instance.get("data"), dict)
    ):
        findings.add("F-011")
    return findings


def _with_known_schema_repairs(value: Any) -> Any:
    if isinstance(value, dict):
        repaired = {key: _with_known_schema_repairs(item) for key, item in value.items()}
        if (
            repaired.get("type") == "object"
            and repaired.get("example") is True
            and repaired.get("default") is True
            and repaired.get("description") == "This property is always true because it's a default field"
        ):
            repaired["type"] = "boolean"
        enum_value = repaired.get("enum")
        items = repaired.get("items")
        if (
            repaired.get("type") == "array"
            and isinstance(enum_value, list)
            and all(isinstance(item, str) for item in enum_value)
            and isinstance(items, dict)
            and items.get("type") == "string"
            and items.get("enum") == enum_value
        ):
            repaired.pop("enum")
        if repaired.get("pattern") == "TIME_FORMAT_HH_MM":
            repaired["pattern"] = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
        all_of = repaired.get("allOf")
        if repaired.get("nullable") is True and _is_single_recurrence_reference(all_of):
            recurrence_all_of = cast(list[JsonObject], all_of)
            repaired.pop("allOf")
            repaired.pop("nullable")
            repaired["anyOf"] = [
                recurrence_all_of[0],
                {"type": "object", "nullable": True, "enum": [None]},
            ]
        union = repaired.get("oneOf")
        if _is_broken_slots_response_union(repaired):
            return _slots_response_schema()
        if _is_default_booking_field_union(union):
            repaired["anyOf"] = repaired.pop("oneOf")
        forward_redirect = repaired.get("forwardParamsSuccessRedirect")
        if (
            isinstance(forward_redirect, dict)
            and forward_redirect.get("type") == "object"
            and forward_redirect.get("nullable") is True
        ):
            forward_redirect["type"] = "boolean"
        rescheduled_by = repaired.get("rescheduledByEmail")
        if _is_exact_booking_nullable_field(rescheduled_by, "string", "rescheduler@example.com"):
            cast(JsonObject, rescheduled_by)["nullable"] = True
        rating = repaired.get("rating")
        if _is_exact_booking_nullable_field(rating, "number", 4):
            cast(JsonObject, rating)["nullable"] = True
        description = repaired.get("description")
        if description == {
            "type": "string",
            "example": "Learn how to integrate scheduling into marketplace.",
        }:
            cast(JsonObject, description)["nullable"] = True
        meeting_url = repaired.get("meetingUrl")
        if meeting_url == {
            "type": "string",
            "description": "Deprecated - rely on 'location' field instead.",
            "example": "https://example.com/recurring-meeting",
            "deprecated": True,
        }:
            cast(JsonObject, meeting_url)["nullable"] = True
        location = repaired.get("location")
        if location == {"type": "string", "example": "https://example.com/meeting"}:
            cast(JsonObject, location)["nullable"] = True
        event_type_id = repaired.get("eventTypeId")
        if event_type_id == {
            "type": "number",
            "example": 50,
            "deprecated": True,
            "description": "Deprecated - rely on 'eventType' object containing the id instead.",
        }:
            cast(JsonObject, event_type_id)["nullable"] = True
        event_type = repaired.get("eventType")
        if event_type == {"$ref": "#/components/schemas/EventType"}:
            repaired["eventType"] = {
                "anyOf": [
                    event_type,
                    {"type": "object", "nullable": True, "enum": [None]},
                ]
            }
        booking_window = repaired.get("bookingWindow")
        if _is_booking_window_array_schema(booking_window):
            booking_window_schema = cast(JsonObject, booking_window)
            repaired["bookingWindow"] = {
                "description": booking_window_schema.get("description"),
                "anyOf": [
                    booking_window_schema,
                    {"$ref": "#/components/schemas/Disabled_2024_06_14"},
                ],
            }
        seats = repaired.get("seats")
        if _is_active_seats_reference(seats):
            seats_schema = cast(JsonObject, seats)
            repaired["seats"] = {
                "anyOf": [
                    seats_schema,
                    {"$ref": "#/components/schemas/Disabled_2024_06_14"},
                ]
            }
        users = repaired.get("users")
        if _is_string_array_schema(users):
            users_schema = cast(JsonObject, users)
            users_schema["items"] = _event_type_user_schema()
        return repaired
    if isinstance(value, list):
        return [_with_known_schema_repairs(item) for item in value]
    return value


def _is_default_booking_field_union(value: object) -> bool:
    if not isinstance(value, list):
        return False
    refs = [item.get("$ref") for item in value if isinstance(item, dict)]
    return len(refs) == len(value) and any(
        isinstance(ref, str) and "DefaultFieldOutput_2024_06_14" in ref for ref in refs
    )


def _is_single_recurrence_reference(value: object) -> bool:
    if not isinstance(value, list) or len(value) != 1 or not isinstance(value[0], dict):
        return False
    ref = value[0].get("$ref")
    return isinstance(ref, str) and ref.endswith("/Recurrence_2024_06_14")


def _is_booking_window_array_schema(value: object) -> bool:
    if not isinstance(value, dict) or value.get("type") != "array":
        return False
    items = value.get("items")
    if not isinstance(items, dict):
        return False
    union = items.get("oneOf")
    if not isinstance(union, list):
        return False
    refs = [item.get("$ref") for item in union if isinstance(item, dict)]
    expected = {"BusinessDaysWindow_2024_06_14", "CalendarDaysWindow_2024_06_14", "RangeWindow_2024_06_14"}
    return {ref.rsplit("/", 1)[-1] for ref in refs if isinstance(ref, str)} == expected


def _is_active_seats_reference(value: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"$ref"}
        and value.get("$ref") == "#/components/schemas/Seats_2024_06_14"
    )


def _is_string_array_schema(value: object) -> bool:
    return (
        isinstance(value, dict)
        and value.get("type") == "array"
        and value.get("items") == {"type": "string"}
        and set(value) == {"type", "items"}
    )


def _event_type_user_schema() -> JsonObject:
    nullable_string: JsonObject = {"type": "string", "nullable": True}
    return {
        "type": "object",
        "properties": {
            "id": {"type": "integer"},
            "name": nullable_string,
            "username": nullable_string,
            "avatarUrl": nullable_string,
            "weekStart": {"type": "string"},
            "brandColor": nullable_string,
            "darkBrandColor": nullable_string,
            "metadata": {"type": "object"},
        },
        "required": [
            "id",
            "name",
            "username",
            "avatarUrl",
            "weekStart",
            "brandColor",
            "darkBrandColor",
            "metadata",
        ],
    }


def _is_broken_slots_response_union(value: object) -> bool:
    if not isinstance(value, dict) or set(value) != {"oneOf"}:
        return False
    union = value.get("oneOf")
    if not isinstance(union, list) or len(union) != 2:
        return False
    titles = {branch.get("title") for branch in union if isinstance(branch, dict)}
    return titles == {
        "Default format (or with format=time)",
        "Range format (when format=range)",
    }


def _slots_response_schema() -> JsonObject:
    time_slot: JsonObject = {
        "type": "object",
        "properties": {"start": {"type": "string", "format": "date-time"}},
        "required": ["start"],
    }
    range_slot: JsonObject = {
        "type": "object",
        "properties": {
            "start": {"type": "string", "format": "date-time"},
            "end": {"type": "string", "format": "date-time"},
        },
        "required": ["start", "end"],
    }
    return {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["success"]},
            "data": {
                "type": "object",
                "additionalProperties": {
                    "type": "array",
                    "items": {"anyOf": [time_slot, range_slot]},
                },
            },
        },
        "required": ["status", "data"],
    }


def _is_exact_booking_nullable_field(value: object, field_type: str, example: object) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"type", "example"}
        and value.get("type") == field_type
        and value.get("example") == example
    )


def _error_summary(error: ValidationError) -> str:
    if len(error.message) <= 240:
        return error.message
    return f"{error.validator} rejected the documented response shape"


def _error_location(error: ValidationError) -> str:
    parts = ["*" if isinstance(part, int) else str(part) for part in error.absolute_path]
    return ".".join(parts) or "<root>"


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the controlled Cal.diy API v2 contract")
    parser.add_argument("--runtime-url", default="http://localhost:5555")
    args = parser.parse_args()
    verify_contracts(args.runtime_url)


if __name__ == "__main__":
    main()
