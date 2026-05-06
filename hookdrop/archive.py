"""Archive module: mark requests as archived and manage archived state."""

ARCHIVE_KEY = "_archived"


def archive_request(store, request_id: str) -> bool:
    """Mark a request as archived. Returns True if found, False otherwise."""
    req = store.get(request_id)
    if req is None:
        return False
    if ARCHIVE_KEY not in req.meta:
        req.meta[ARCHIVE_KEY] = True
    return True


def unarchive_request(store, request_id: str) -> bool:
    """Remove archived status from a request. Returns True if found."""
    req = store.get(request_id)
    if req is None:
        return False
    req.meta.pop(ARCHIVE_KEY, None)
    return True


def is_archived(store, request_id: str) -> bool:
    """Return True if the request is archived."""
    req = store.get(request_id)
    if req is None:
        return False
    return bool(req.meta.get(ARCHIVE_KEY, False))


def list_archived(store) -> list:
    """Return all archived requests."""
    return [r for r in store.all() if r.meta.get(ARCHIVE_KEY, False)]


def list_active(store) -> list:
    """Return all non-archived requests."""
    return [r for r in store.all() if not r.meta.get(ARCHIVE_KEY, False)]


def clear_archived(store) -> int:
    """Delete all archived requests from the store. Returns count removed."""
    archived = list_archived(store)
    for req in archived:
        store.delete(req.id)
    return len(archived)
