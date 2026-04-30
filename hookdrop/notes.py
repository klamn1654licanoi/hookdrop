"""Notes module: attach and retrieve human-readable notes on webhook requests."""

from hookdrop.storage import RequestStore


def add_note(store: RequestStore, request_id: str, note: str) -> bool:
    """Add or replace a note on a request. Returns True if request found."""
    req = store.get(request_id)
    if req is None:
        return False
    if req.meta is None:
        req.meta = {}
    req.meta["note"] = note
    return True


def get_note(store: RequestStore, request_id: str) -> str | None:
    """Return the note for a request, or None if not set or not found."""
    req = store.get(request_id)
    if req is None:
        return None
    if req.meta is None:
        return None
    return req.meta.get("note")


def remove_note(store: RequestStore, request_id: str) -> bool:
    """Remove the note from a request. Returns True if request found."""
    req = store.get(request_id)
    if req is None:
        return False
    if req.meta and "note" in req.meta:
        del req.meta["note"]
    return True


def requests_with_notes(store: RequestStore) -> list:
    """Return all requests that have a non-empty note attached."""
    result = []
    for req in store.all():
        if req.meta and req.meta.get("note"):
            result.append(req)
    return result
