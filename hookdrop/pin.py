from hookdrop.storage import RequestStore

PINNED_KEY = "__pinned__"


def pin_request(store: RequestStore, request_id: str) -> bool:
    """Pin a request by ID. Returns True if successful, False if not found."""
    req = store.get(request_id)
    if req is None:
        return False
    meta = store.meta.setdefault(request_id, {})
    meta[PINNED_KEY] = True
    return True


def unpin_request(store: RequestStore, request_id: str) -> bool:
    """Unpin a request by ID. Returns True if successful, False if not found."""
    req = store.get(request_id)
    if req is None:
        return False
    meta = store.meta.get(request_id, {})
    meta.pop(PINNED_KEY, None)
    return True


def is_pinned(store: RequestStore, request_id: str) -> bool:
    """Return True if the request is pinned."""
    meta = store.meta.get(request_id, {})
    return bool(meta.get(PINNED_KEY, False))


def list_pinned(store: RequestStore) -> list:
    """Return all pinned requests."""
    return [
        req for req in store.all()
        if is_pinned(store, req.id)
    ]


def clear_pins(store: RequestStore) -> int:
    """Remove all pins. Returns count of unpinned requests."""
    count = 0
    for request_id, meta in store.meta.items():
        if meta.pop(PINNED_KEY, None):
            count += 1
    return count
