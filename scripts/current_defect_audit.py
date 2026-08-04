#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HTTP_METHODS = {"delete", "get", "head", "options", "patch", "post", "put", "trace"}
DEFAULT_FIELD_SCHEMAS = {
    "EmailDefaultFieldOutput_2024_06_14",
    "GuestsDefaultFieldOutput_2024_06_14",
    "LocationDefaultFieldOutput_2024_06_14",
    "NameDefaultFieldOutput_2024_06_14",
    "NotesDefaultFieldOutput_2024_06_14",
    "RescheduleReasonDefaultFieldOutput_2024_06_14",
    "TitleDefaultFieldOutput_2024_06_14",
}
WEEKDAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def duplicate_operation_ids(spec: dict[str, Any]) -> list[dict[str, Any]]:
    occurrences: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for path, path_item in spec.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if isinstance(operation_id, str):
                occurrences[operation_id].append({"method": method.upper(), "path": path})
    return [
        {"operationId": operation_id, "operations": operations}
        for operation_id, operations in sorted(occurrences.items())
        if len(operations) > 1
    ]


def default_field_mismatches(spec: dict[str, Any]) -> list[dict[str, Any]]:
    schemas = spec.get("components", {}).get("schemas", {})
    mismatches: list[dict[str, Any]] = []
    for name in sorted(DEFAULT_FIELD_SCHEMAS):
        schema = schemas.get(name, {})
        is_default = schema.get("properties", {}).get("isDefault", {})
        if (
            is_default.get("type") == "object"
            and is_default.get("default") is True
            and is_default.get("example") is True
        ):
            mismatches.append(
                {
                    "schema": name,
                    "declaredType": "object",
                    "default": True,
                    "example": True,
                }
            )
    return mismatches


def historical_contract_triage(spec: dict[str, Any]) -> list[dict[str, str]]:
    paths = spec.get("paths", {})
    schemas = spec.get("components", {}).get("schemas", {})
    event_type = schemas.get("EventTypeOutput_2024_06_14", {}).get("properties", {})
    booking = schemas.get("BookingOutput_2024_08_13", {}).get("properties", {})
    slots = (
        paths.get("/v2/slots", {})
        .get("get", {})
        .get("responses", {})
        .get("200", {})
        .get("content", {})
        .get("application/json", {})
        .get("schema", {})
    )

    has_days_array_enum = False
    has_time_placeholder = False
    for schema in schemas.values():
        if not isinstance(schema, dict):
            continue
        for property_schema in schema.get("properties", {}).values():
            if not isinstance(property_schema, dict):
                continue
            enum = property_schema.get("enum")
            if property_schema.get("type") == "array" and isinstance(enum, list):
                has_days_array_enum |= set(enum) == WEEKDAYS
            has_time_placeholder |= property_schema.get("pattern") == "TIME_FORMAT_HH_MM"

    results = [
        {
            "finding": "F-001",
            "status": "not-present",
            "basis": "The affected organization-team route is absent from current main.",
        }
        if "/v2/organizations/{orgId}/teams/{teamId}" not in paths
        else {
            "finding": "F-001",
            "status": "condition-present",
            "basis": "The affected route remains present; parameter resolution requires review.",
        },
        {
            "finding": "F-002",
            "status": "reproduced-current-source-and-contract"
            if len(default_field_mismatches(spec)) == len(DEFAULT_FIELD_SCHEMAS)
            else "changed",
            "basis": "Seven output schemas contradict their boolean default/example and current source type.",
        },
        {
            "finding": "F-003",
            "status": "condition-present" if has_days_array_enum else "not-present",
            "basis": "The current contract no longer puts weekday enum values on the days array."
            if not has_days_array_enum
            else "A weekday enum remains attached to an array schema.",
        },
        {
            "finding": "F-004",
            "status": "condition-present" if has_time_placeholder else "not-present",
            "basis": "The current contract no longer contains the literal TIME_FORMAT_HH_MM pattern."
            if not has_time_placeholder
            else "The literal TIME_FORMAT_HH_MM pattern remains present.",
        },
    ]

    conditions = {
        "F-005": "Current booking-field union still needs runtime validation after F-002 is corrected.",
        "F-006": "recurrence remains nullable with a non-nullable allOf reference.",
        "F-007": "forwardParamsSuccessRedirect remains a nullable object schema.",
        "F-008": "bookingWindow output still omits the disabled alternative.",
        "F-009": "seats output still directly references the active seats schema.",
        "F-010": "event-type users remain documented as an array of strings.",
        "F-011": "slots 200 schema still places date maps at the root and default items are strings.",
        "F-012": "booking rescheduledByEmail and rating remain non-nullable when present.",
        "F-013": "booking description, meetingUrl and location remain non-nullable strings.",
        "F-014": "booking eventTypeId and eventType remain non-nullable when present.",
    }
    structural_presence = {
        "F-006": event_type.get("recurrence", {}).get("nullable") is True
        and "allOf" in event_type.get("recurrence", {}),
        "F-007": event_type.get("forwardParamsSuccessRedirect", {}).get("type") == "object",
        "F-008": event_type.get("bookingWindow", {}).get("type") == "array",
        "F-009": event_type.get("seats", {}).get("$ref", "").endswith("/Seats_2024_06_14"),
        "F-010": event_type.get("users", {}).get("items", {}).get("type") == "string",
        "F-011": isinstance(slots.get("oneOf"), list),
        "F-012": all(
            not booking.get(name, {}).get("nullable", False)
            for name in ("rescheduledByEmail", "rating")
        ),
        "F-013": all(
            not booking.get(name, {}).get("nullable", False)
            for name in ("description", "meetingUrl", "location")
        ),
        "F-014": all(
            not booking.get(name, {}).get("nullable", False)
            for name in ("eventTypeId", "eventType")
        ),
    }
    results.append(
        {
            "finding": "F-005",
            "status": "runtime-not-reproduced",
            "basis": conditions["F-005"],
        }
    )
    for finding in ("F-006", "F-007", "F-008", "F-009", "F-010", "F-011", "F-012", "F-013", "F-014"):
        results.append(
            {
                "finding": finding,
                "status": "contract-condition-present-runtime-not-reproduced"
                if structural_presence[finding]
                else "not-present",
                "basis": conditions[finding],
            }
        )
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit current public Cal.diy source for Phase 6 defects")
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--current-sha", required=True)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-f]{40}", args.current_sha):
        raise SystemExit("current SHA must be a full lowercase commit hash")
    spec_path = args.source_root / "docs/api-reference/v2/openapi.json"
    source_path = (
        args.source_root
        / "packages/platform/types/event-types/event-types_2024_06_14/outputs/booking-fields.output.ts"
    )
    spec_bytes = spec_path.read_bytes()
    spec = json.loads(spec_bytes)
    source = source_path.read_text(encoding="utf-8") if source_path.is_file() else ""
    duplicates = duplicate_operation_ids(spec)
    field_mismatches = default_field_mismatches(spec)
    source_boolean_classes = source.count("isDefault = true;")

    result = {
        "schemaVersion": 1,
        "checkedAt": datetime.now(UTC).isoformat(),
        "publicMainCommit": args.current_sha,
        "hostedCalComTested": False,
        "openApiSha256": hashlib.sha256(spec_bytes).hexdigest(),
        "observations": {
            "DEFECT-001": {
                "status": "reproduced" if duplicates else "not-reproduced",
                "duplicateOperationIds": duplicates,
            },
            "DEFECT-002": {
                "status": "reproduced"
                if field_mismatches and source_boolean_classes >= len(field_mismatches)
                else "not-reproduced",
                "schemas": field_mismatches,
                "sourceBooleanClassCount": source_boolean_classes,
            },
        },
        "historicalContractTriage": historical_contract_triage(spec),
    }
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    lines = [
        "### Current public Cal.diy defect audit",
        "",
        f"Audited public `main` at `{args.current_sha}`; hosted Cal.com was not tested.",
        f"OpenAPI SHA-256: `{result['openApiSha256']}`.",
        "",
        f"- DEFECT-001: {len(duplicates)} duplicate operation IDs observed",
        f"- DEFECT-002: {len(field_mismatches)} default-field type contradictions observed",
        "- Historical runtime and UI findings were not promoted without current runtime evidence",
    ]
    args.markdown_output.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
