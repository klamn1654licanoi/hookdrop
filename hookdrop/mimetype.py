"""MIME type detection and filtering for webhook requests."""

import json

_MIMETYPE_OVERRIDES = {}


def detect_mimetype(request) -> str:
    """Detect the MIME type of a request based on Content-Type header."""
    content_type = request.headers.get("content-type", "")
    if ";" in content_type:
        content_type = content_type.split(";")[0].strip()
    return content_type.lower() if content_type else "application/octet-stream"


def set_mimetype_override(request_id: str, mimetype: str) -> None:
    """Manually override the detected MIME type for a request."""
    _MIMETYPE_OVERRIDES[request_id] = mimetype


def get_mimetype_override(request_id: str) -> str | None:
    """Get any manually set MIME type override for a request."""
    return _MIMETYPE_OVERRIDES.get(request_id)


def remove_mimetype_override(request_id: str) -> bool:
    """Remove a MIME type override. Returns True if it existed."""
    if request_id in _MIMETYPE_OVERRIDES:
        del _MIMETYPE_OVERRIDES[request_id]
        return True
    return False


def clear_mimetype_overrides() -> None:
    """Clear all MIME type overrides."""
    _MIMETYPE_OVERRIDES.clear()


def effective_mimetype(request) -> str:
    """Return the effective MIME type, preferring manual override."""
    override = get_mimetype_override(request.id)
    return override if override else detect_mimetype(request)


def filter_by_mimetype(requests: list, mimetype: str) -> list:
    """Filter requests by effective MIME type (substring match)."""
    mimetype_lower = mimetype.lower()
    return [r for r in requests if mimetype_lower in effective_mimetype(r)]


def is_json(request) -> bool:
    """Return True if the request appears to have a JSON body."""
    mt = effective_mimetype(request)
    if "json" not in mt:
        return False
    try:
        json.loads(request.body)
        return True
    except (ValueError, TypeError):
        return False


def is_form(request) -> bool:
    """Return True if the request is form-encoded."""
    mt = effective_mimetype(request)
    return "application/x-www-form-urlencoded" in mt or "multipart/form-data" in mt


def mimetype_summary(requests: list) -> dict:
    """Return a count of requests grouped by effective MIME type."""
    summary: dict = {}
    for r in requests:
        mt = effective_mimetype(r)
        summary[mt] = summary.get(mt, 0) + 1
    return summary
