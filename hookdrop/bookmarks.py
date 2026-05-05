from typing import Optional
from hookdrop.storage import RequestStore

_bookmarks: dict[str, str] = {}  # label -> request_id


def add_bookmark(store: RequestStore, request_id: str, label: str) -> bool:
    """Bookmark a request with a human-readable label."""
    req = store.get(request_id)
    if req is None:
        return False
    _bookmarks[label] = request_id
    return True


def remove_bookmark(label: str) -> bool:
    """Remove a bookmark by label."""
    if label not in _bookmarks:
        return False
    del _bookmarks[label]
    return True


def get_bookmark(store: RequestStore, label: str) -> Optional[object]:
    """Retrieve the request associated with a bookmark label."""
    request_id = _bookmarks.get(label)
    if request_id is None:
        return None
    return store.get(request_id)


def list_bookmarks() -> dict[str, str]:
    """Return all bookmarks as {label: request_id}."""
    return dict(_bookmarks)


def clear_bookmarks() -> None:
    """Clear all bookmarks (useful for testing)."""
    _bookmarks.clear()
