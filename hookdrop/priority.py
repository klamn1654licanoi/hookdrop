from hookdrop.storage import RequestStore

PRIORITY_LEVELS = ("low", "normal", "high", "critical")
_priorities: dict[str, str] = {}


def set_priority(store: RequestStore, request_id: str, level: str) -> bool:
    """Set a priority level for a request. Returns False if request not found."""
    if level not in PRIORITY_LEVELS:
        raise ValueError(f"Invalid priority level '{level}'. Must be one of {PRIORITY_LEVELS}.")
    req = store.get(request_id)
    if req is None:
        return False
    _priorities[request_id] = level
    return True


def get_priority(request_id: str) -> str | None:
    """Get the priority level for a request, or None if not set."""
    return _priorities.get(request_id)


def remove_priority(request_id: str) -> bool:
    """Remove the priority for a request. Returns False if not set."""
    if request_id in _priorities:
        del _priorities[request_id]
        return True
    return False


def filter_by_priority(store: RequestStore, level: str) -> list:
    """Return all requests with the given priority level."""
    if level not in PRIORITY_LEVELS:
        raise ValueError(f"Invalid priority level '{level}'.")
    return [
        req for req in store.all()
        if _priorities.get(req.id) == level
    ]


def list_all_priorities(store: RequestStore) -> dict[str, str]:
    """Return a mapping of request_id -> priority for all requests that have one."""
    all_ids = {req.id for req in store.all()}
    return {rid: lvl for rid, lvl in _priorities.items() if rid in all_ids}


def clear_priorities() -> None:
    """Clear all stored priorities (useful for testing)."""
    _priorities.clear()
