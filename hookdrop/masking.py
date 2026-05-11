"""Field masking for sensitive webhook request data."""

import re
from typing import Optional

_mask_rules: dict[str, str] = {}  # field_name -> mask pattern (e.g. "****" or regex replace)

DEFAULT_MASK = "***MASKED***"


def add_mask_rule(field: str, mask: str = DEFAULT_MASK) -> None:
    """Register a field name to be masked in request bodies and headers."""
    _mask_rules[field.lower()] = mask


def remove_mask_rule(field: str) -> bool:
    """Remove a mask rule. Returns True if it existed."""
    return _mask_rules.pop(field.lower(), None) is not None


def list_mask_rules() -> dict[str, str]:
    """Return a copy of all active mask rules."""
    return dict(_mask_rules)


def clear_mask_rules() -> None:
    """Remove all mask rules."""
    _mask_rules.clear()


def mask_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return a copy of headers with masked values for matching fields."""
    result = {}
    for key, value in headers.items():
        mask = _mask_rules.get(key.lower())
        result[key] = mask if mask is not None else value
    return result


def mask_body(body: str) -> str:
    """Apply mask rules to a JSON-like body string using regex substitution."""
    result = body
    for field, mask in _mask_rules.items():
        # Match both quoted string values and numeric values for the field
        pattern = r'(?<="' + re.escape(field) + r'"\s*:\s*)"[^"]*"'
        replacement = f'"{mask}"'
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def mask_request(request_dict: dict) -> dict:
    """Return a copy of a request dict with headers and body masked."""
    import copy
    masked = copy.deepcopy(request_dict)
    if "headers" in masked and isinstance(masked["headers"], dict):
        masked["headers"] = mask_headers(masked["headers"])
    if "body" in masked and isinstance(masked["body"], str):
        masked["body"] = mask_body(masked["body"])
    return masked
