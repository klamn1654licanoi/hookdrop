from datetime import datetime, timezone
from typing import Optional
from hookdrop.storage import RequestStore

_retry_policy: dict = {}
_retry_history: dict = {}


def set_retry_policy(request_id: str, store: RequestStore, max_attempts: int = 3, delay_seconds: float = 5.0) -> bool:
    """Set a retry policy for a given request ID."""
    req = store.get(request_id)
    if req is None:
        return False
    _retry_policy[request_id] = {
        "max_attempts": max_attempts,
        "delay_seconds": delay_seconds,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return True


def get_retry_policy(request_id: str) -> Optional[dict]:
    """Return the retry policy for a request, or None."""
    return _retry_policy.get(request_id)


def remove_retry_policy(request_id: str) -> bool:
    """Remove the retry policy for a request."""
    if request_id in _retry_policy:
        del _retry_policy[request_id]
        return True
    return False


def record_retry_attempt(request_id: str, success: bool, status_code: Optional[int] = None) -> None:
    """Record a retry attempt result for a request."""
    if request_id not in _retry_history:
        _retry_history[request_id] = []
    _retry_history[request_id].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "success": success,
        "status_code": status_code,
    })


def get_retry_history(request_id: str) -> list:
    """Return the list of retry attempt records for a request."""
    return _retry_history.get(request_id, [])


def retry_summary(request_id: str) -> dict:
    """Return a summary of retry state for a request."""
    policy = get_retry_policy(request_id)
    history = get_retry_history(request_id)
    attempts = len(history)
    successes = sum(1 for h in history if h["success"])
    return {
        "request_id": request_id,
        "policy": policy,
        "attempts": attempts,
        "successes": successes,
        "failures": attempts - successes,
        "exhausted": policy is not None and attempts >= policy["max_attempts"],
    }


def clear_retry_state() -> None:
    """Clear all retry policies and history (for testing)."""
    _retry_policy.clear()
    _retry_history.clear()
