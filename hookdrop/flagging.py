"""Request flagging — mark requests with named flags for triage and review."""

from hookdrop.storage import RequestStore

# flag_store: { request_id: set of flag names }
_flags: dict[str, set] = {}


def add_flag(store: RequestStore, request_id: str, flag: str) -> bool:
    """Add a flag to a request. Returns False if request not found."""
    if store.get(request_id) is None:
        return False
    flag = flag.strip().lower()
    if not flag:
        raise ValueError("Flag name must not be empty")
    _flags.setdefault(request_id, set()).add(flag)
    return True


def remove_flag(store: RequestStore, request_id: str, flag: str) -> bool:
    """Remove a flag from a request. Returns False if not found."""
    flag = flag.strip().lower()
    if request_id not in _flags or flag not in _flags[request_id]:
        return False
    _flags[request_id].discard(flag)
    if not _flags[request_id]:
        del _flags[request_id]
    return True


def get_flags(request_id: str) -> list[str]:
    """Return all flags for a request."""
    return sorted(_flags.get(request_id, set()))


def has_flag(request_id: str, flag: str) -> bool:
    """Check whether a request has a specific flag."""
    return flag.strip().lower() in _flags.get(request_id, set())


def filter_by_flag(store: RequestStore, flag: str) -> list:
    """Return all requests that carry the given flag."""
    flag = flag.strip().lower()
    result = []
    for req in store.all():
        if flag in _flags.get(req.id, set()):
            result.append(req)
    return result


def list_all_flags() -> dict[str, list[str]]:
    """Return a mapping of request_id -> sorted list of flags."""
    return {rid: sorted(flags) for rid, flags in _flags.items() if flags}


def clear_flags():
    """Remove all flags (used in tests)."""
    _flags.clear()
