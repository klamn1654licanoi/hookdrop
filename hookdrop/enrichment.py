"""Request enrichment: attach arbitrary key-value metadata to requests."""

from typing import Any, Dict, Optional

# request_id -> {key: value}
_enrichments: Dict[str, Dict[str, Any]] = {}


def set_enrichment(store, request_id: str, key: str, value: Any) -> bool:
    """Set an enrichment key-value pair on a request. Returns False if not found."""
    req = store.get(request_id)
    if req is None:
        return False
    if request_id not in _enrichments:
        _enrichments[request_id] = {}
    _enrichments[request_id][key] = value
    return True


def get_enrichment(request_id: str, key: str) -> Optional[Any]:
    """Get a single enrichment value for a request."""
    return _enrichments.get(request_id, {}).get(key)


def get_all_enrichments(request_id: str) -> Dict[str, Any]:
    """Return all enrichment data for a request."""
    return dict(_enrichments.get(request_id, {}))


def remove_enrichment(request_id: str, key: str) -> bool:
    """Remove a single enrichment key. Returns False if key did not exist."""
    if request_id in _enrichments and key in _enrichments[request_id]:
        del _enrichments[request_id][key]
        if not _enrichments[request_id]:
            del _enrichments[request_id]
        return True
    return False


def clear_enrichments(request_id: str) -> None:
    """Remove all enrichment data for a request."""
    _enrichments.pop(request_id, None)


def filter_by_enrichment(store, key: str, value: Any) -> list:
    """Return all requests that have a specific enrichment key-value pair."""
    results = []
    for req in store.all():
        if _enrichments.get(req.id, {}).get(key) == value:
            results.append(req)
    return results


def list_all_enrichments() -> Dict[str, Dict[str, Any]]:
    """Return all enrichment data across all requests."""
    return {k: dict(v) for k, v in _enrichments.items()}


def reset_enrichments() -> None:
    """Clear all enrichment data (useful for testing)."""
    _enrichments.clear()
