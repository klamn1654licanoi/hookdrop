"""Group webhook requests into named collections for organization."""

from hookdrop.storage import RequestStore

_groups: dict[str, set[str]] = {}


def create_group(name: str) -> dict:
    """Create a new empty group."""
    if name in _groups:
        return {"created": False, "name": name}
    _groups[name] = set()
    return {"created": True, "name": name}


def delete_group(name: str) -> bool:
    """Delete a group by name. Returns True if it existed."""
    if name in _groups:
        del _groups[name]
        return True
    return False


def add_to_group(store: RequestStore, name: str, request_id: str) -> bool:
    """Add a request ID to a group. Returns False if group or request not found."""
    if name not in _groups:
        return False
    req = store.get(request_id)
    if req is None:
        return False
    _groups[name].add(request_id)
    return True


def remove_from_group(name: str, request_id: str) -> bool:
    """Remove a request ID from a group. Returns False if group not found."""
    if name not in _groups:
        return False
    _groups[name].discard(request_id)
    return True


def get_group(store: RequestStore, name: str) -> list | None:
    """Return all requests in a group, or None if group doesn't exist."""
    if name not in _groups:
        return None
    result = []
    for rid in list(_groups[name]):
        req = store.get(rid)
        if req is not None:
            result.append(req.to_dict())
        else:
            _groups[name].discard(rid)
    return result


def list_groups() -> list[dict]:
    """Return all group names and their sizes."""
    return [{"name": name, "size": len(ids)} for name, ids in _groups.items()]


def clear_all_groups() -> None:
    """Remove all groups (used in tests)."""
    _groups.clear()
