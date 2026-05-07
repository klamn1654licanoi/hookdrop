"""Correlation ID tracking for webhook requests."""

from typing import Optional

# Maps request_id -> correlation_id
_correlations: dict[str, str] = {}
# Maps correlation_id -> list of request_ids
_groups: dict[str, list[str]] = {}


def set_correlation(store, request_id: str, correlation_id: str) -> bool:
    """Associate a request with a correlation ID."""
    if store.get(request_id) is None:
        return False
    _correlations[request_id] = correlation_id
    if correlation_id not in _groups:
        _groups[correlation_id] = []
    if request_id not in _groups[correlation_id]:
        _groups[correlation_id].append(request_id)
    return True


def get_correlation(request_id: str) -> Optional[str]:
    """Get the correlation ID for a given request."""
    return _correlations.get(request_id)


def remove_correlation(request_id: str) -> bool:
    """Remove the correlation ID association for a request."""
    if request_id not in _correlations:
        return False
    correlation_id = _correlations.pop(request_id)
    if correlation_id in _groups:
        _groups[correlation_id] = [
            rid for rid in _groups[correlation_id] if rid != request_id
        ]
        if not _groups[correlation_id]:
            del _groups[correlation_id]
    return True


def get_correlated_requests(store, correlation_id: str) -> list:
    """Return all requests sharing the same correlation ID."""
    request_ids = _groups.get(correlation_id, [])
    results = []
    for rid in request_ids:
        req = store.get(rid)
        if req is not None:
            results.append(req)
    return results


def list_all_correlations() -> dict[str, list[str]]:
    """Return a mapping of correlation_id -> [request_ids]."""
    return {k: list(v) for k, v in _groups.items()}


def clear_correlations() -> None:
    """Clear all correlation data."""
    _correlations.clear()
    _groups.clear()
