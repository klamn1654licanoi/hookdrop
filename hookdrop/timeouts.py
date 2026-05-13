"""Request timeout tracking — flag requests that took too long to process."""

from typing import Optional
from hookdrop.storage import RequestStore

_timeout_rules: dict[str, float] = {}  # path_prefix -> max_seconds
_timeout_flags: dict[str, bool] = {}   # request_id -> timed_out


def set_timeout_rule(path_prefix: str, max_seconds: float) -> None:
    """Register a timeout threshold for a path prefix."""
    if max_seconds <= 0:
        raise ValueError("max_seconds must be positive")
    _timeout_rules[path_prefix] = max_seconds


def get_timeout_rule(path_prefix: str) -> Optional[float]:
    """Return the timeout threshold for a path prefix, or None."""
    return _timeout_rules.get(path_prefix)


def remove_timeout_rule(path_prefix: str) -> bool:
    """Remove a timeout rule. Returns True if it existed."""
    if path_prefix in _timeout_rules:
        del _timeout_rules[path_prefix]
        return True
    return False


def list_timeout_rules() -> dict[str, float]:
    """Return all registered timeout rules."""
    return dict(_timeout_rules)


def clear_timeout_rules() -> None:
    """Remove all timeout rules and flags."""
    _timeout_rules.clear()
    _timeout_flags.clear()


def evaluate_request(store: RequestStore, request_id: str) -> Optional[bool]:
    """Check if a request exceeded any matching timeout rule.

    Returns True if timed out, False if within limit, None if no rule matched.
    """
    req = store.get(request_id)
    if req is None:
        return None

    duration = getattr(req, "duration", None)
    if duration is None:
        return None

    matched_threshold = None
    for prefix, threshold in _timeout_rules.items():
        if req.path.startswith(prefix):
            if matched_threshold is None or threshold < matched_threshold:
                matched_threshold = threshold

    if matched_threshold is None:
        return None

    timed_out = duration > matched_threshold
    _timeout_flags[request_id] = timed_out
    return timed_out


def is_timed_out(request_id: str) -> Optional[bool]:
    """Return the cached timeout flag for a request, or None if not evaluated."""
    return _timeout_flags.get(request_id)


def list_timed_out(store: RequestStore) -> list[dict]:
    """Return all requests flagged as timed out."""
    result = []
    for req in store.all():
        if evaluate_request(store, req.id) is True:
            result.append({"id": req.id, "path": req.path, "duration": getattr(req, "duration", None)})
    return result
