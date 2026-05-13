"""Request annotations — attach structured key/value metadata to requests."""

from typing import Any, Dict, List, Optional
from hookdrop.storage import RequestStore

_annotations: Dict[str, Dict[str, Any]] = {}


def set_annotation(store: RequestStore, request_id: str, key: str, value: Any) -> None:
    """Set an annotation key/value on a request."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found")
    if request_id not in _annotations:
        _annotations[request_id] = {}
    _annotations[request_id][key] = value


def get_annotation(store: RequestStore, request_id: str, key: str) -> Optional[Any]:
    """Get a single annotation value by key."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found")
    return _annotations.get(request_id, {}).get(key)


def get_all_annotations(store: RequestStore, request_id: str) -> Dict[str, Any]:
    """Return all annotations for a request."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found")
    return dict(_annotations.get(request_id, {}))


def remove_annotation(store: RequestStore, request_id: str, key: str) -> bool:
    """Remove a single annotation key. Returns True if removed, False if not present."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found")
    if request_id in _annotations and key in _annotations[request_id]:
        del _annotations[request_id][key]
        if not _annotations[request_id]:
            del _annotations[request_id]
        return True
    return False


def clear_annotations(request_id: str) -> None:
    """Remove all annotations for a request."""
    _annotations.pop(request_id, None)


def filter_by_annotation(store: RequestStore, key: str, value: Any) -> List[str]:
    """Return request IDs whose annotation key matches value."""
    return [
        rid for rid, ann in _annotations.items()
        if ann.get(key) == value and store.get(rid) is not None
    ]


def list_all_annotations() -> Dict[str, Dict[str, Any]]:
    """Return a copy of all annotations across all requests."""
    return {rid: dict(ann) for rid, ann in _annotations.items()}


def reset_annotations() -> None:
    """Clear all annotation data (used in tests)."""
    _annotations.clear()
