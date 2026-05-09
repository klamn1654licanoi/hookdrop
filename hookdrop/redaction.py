"""Redaction support: mask sensitive fields in request headers and body."""

import re
from typing import Optional

_redaction_rules: dict[str, str] = {}
_REDACTED = "[REDACTED]"


def add_rule(field: str, pattern: Optional[str] = None) -> None:
    """Register a field name (header or body key) to redact, with optional regex pattern."""
    _redaction_rules[field.lower()] = pattern or ""


def remove_rule(field: str) -> bool:
    key = field.lower()
    if key in _redaction_rules:
        del _redaction_rules[key]
        return True
    return False


def list_rules() -> dict[str, str]:
    return dict(_redaction_rules)


def clear_rules() -> None:
    _redaction_rules.clear()


def redact_headers(headers: dict) -> dict:
    """Return a copy of headers with sensitive values masked."""
    result = {}
    for k, v in headers.items():
        if k.lower() in _redaction_rules:
            pattern = _redaction_rules[k.lower()]
            if pattern:
                result[k] = re.sub(pattern, _REDACTED, v)
            else:
                result[k] = _REDACTED
        else:
            result[k] = v
    return result


def redact_body(body: str) -> str:
    """Apply pattern-based redaction rules to a raw body string."""
    result = body
    for field, pattern in _redaction_rules.items():
        if pattern:
            result = re.sub(pattern, _REDACTED, result)
        else:
            # Attempt naive key=value and "key":"value" replacements
            result = re.sub(
                rf'("{re.escape(field)}"\s*:\s*")[^"]*"',
                rf'\g<1>{_REDACTED}"',
                result,
                flags=re.IGNORECASE,
            )
    return result


def apply_redaction(request_dict: dict) -> dict:
    """Return a redacted copy of a request dict (headers + body)."""
    out = dict(request_dict)
    out["headers"] = redact_headers(out.get("headers") or {})
    out["body"] = redact_body(out.get("body") or "")
    return out
