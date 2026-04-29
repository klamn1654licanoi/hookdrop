"""Request filtering utilities for hookdrop."""

from typing import Optional


def matches_method(request: dict, method: Optional[str]) -> bool:
    """Check if a request matches the given HTTP method filter."""
    if method is None:
        return True
    return request.get("method", "").upper() == method.upper()


def matches_path(request: dict, path: Optional[str]) -> bool:
    """Check if a request matches the given path filter (substring match)."""
    if path is None:
        return True
    return path in request.get("path", "")


def matches_header(request: dict, header_key: str, header_value: Optional[str]) -> bool:
    """Check if a request contains a specific header (and optionally a value)."""
    headers = {k.lower(): v for k, v in request.get("headers", {}).items()}
    key = header_key.lower()
    if key not in headers:
        return False
    if header_value is None:
        return True
    return headers[key] == header_value


def matches_body(request: dict, body_contains: Optional[str]) -> bool:
    """Check if a request body contains the given substring."""
    if body_contains is None:
        return True
    body = request.get("body", "") or ""
    return body_contains in body


def apply_filters(
    requests: list,
    method: Optional[str] = None,
    path: Optional[str] = None,
    header_key: Optional[str] = None,
    header_value: Optional[str] = None,
    body_contains: Optional[str] = None,
) -> list:
    """Apply all active filters to a list of request dicts."""
    results = []
    for req in requests:
        if not matches_method(req, method):
            continue
        if not matches_path(req, path):
            continue
        if header_key and not matches_header(req, header_key, header_value):
            continue
        if not matches_body(req, body_contains):
            continue
        results.append(req)
    return results
