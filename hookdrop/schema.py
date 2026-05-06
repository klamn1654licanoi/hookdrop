"""Schema validation for incoming webhook requests."""

import json
import re
from typing import Optional


_schemas = {}  # path_pattern -> schema dict


def register_schema(path_pattern: str, schema: dict) -> None:
    """Register a JSON schema for a given path pattern."""
    _schemas[path_pattern] = schema


def unregister_schema(path_pattern: str) -> bool:
    """Remove a registered schema. Returns True if it existed."""
    if path_pattern in _schemas:
        del _schemas[path_pattern]
        return True
    return False


def get_schema(path_pattern: str) -> Optional[dict]:
    """Retrieve a registered schema by path pattern."""
    return _schemas.get(path_pattern)


def list_schemas() -> dict:
    """Return all registered schemas."""
    return dict(_schemas)


def _check_required(body: dict, required: list) -> list:
    return [f"Missing required field: '{f}'" for f in required if f not in body]


def _check_types(body: dict, properties: dict) -> list:
    errors = []
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    for field, spec in properties.items():
        if field not in body:
            continue
        expected = spec.get("type")
        if expected and expected in type_map:
            if not isinstance(body[field], type_map[expected]):
                errors.append(f"Field '{field}' expected type '{expected}'")
    return errors


def validate_body(body_raw: str, schema: dict) -> tuple[bool, list]:
    """Validate a raw JSON body string against a schema dict.
    Returns (is_valid, list_of_errors).
    """
    try:
        body = json.loads(body_raw) if isinstance(body_raw, str) else body_raw
    except (json.JSONDecodeError, TypeError):
        return False, ["Body is not valid JSON"]

    if not isinstance(body, dict):
        return False, ["Body must be a JSON object"]

    errors = []
    errors += _check_required(body, schema.get("required", []))
    errors += _check_types(body, schema.get("properties", {}))
    return len(errors) == 0, errors


def validate_request(path: str, body: str) -> tuple[bool, list]:
    """Find a matching schema for the path and validate the body.
    Returns (is_valid, errors). If no schema matches, returns (True, []).
    """
    for pattern, schema in _schemas.items():
        if re.search(pattern, path):
            return validate_body(body, schema)
    return True, []


def clear_schemas() -> None:
    """Remove all registered schemas."""
    _schemas.clear()
