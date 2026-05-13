"""Track replay attempts and outcomes for webhook requests."""

from datetime import datetime, timezone
from typing import Optional

# replay_log: {request_id: [attempt, ...]}
_replay_log: dict[str, list[dict]] = {}


def record_replay(request_id: str, target_url: str, status_code: Optional[int], error: Optional[str] = None) -> dict:
    """Record a replay attempt for a given request."""
    attempt = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target_url": target_url,
        "status_code": status_code,
        "error": error,
        "success": error is None and status_code is not None and status_code < 400,
    }
    _replay_log.setdefault(request_id, []).append(attempt)
    return attempt


def get_replay_history(request_id: str) -> list[dict]:
    """Return all replay attempts for a request."""
    return list(_replay_log.get(request_id, []))


def clear_replay_history(request_id: str) -> bool:
    """Clear replay history for a specific request. Returns True if existed."""
    if request_id in _replay_log:
        del _replay_log[request_id]
        return True
    return False


def list_all_replayed() -> dict[str, list[dict]]:
    """Return a copy of the full replay log."""
    return {rid: list(attempts) for rid, attempts in _replay_log.items()}


def replay_summary(request_id: str) -> dict:
    """Return a summary of replay attempts for a request."""
    history = get_replay_history(request_id)
    if not history:
        return {"request_id": request_id, "total": 0, "successes": 0, "failures": 0, "last": None}
    successes = sum(1 for a in history if a["success"])
    return {
        "request_id": request_id,
        "total": len(history),
        "successes": successes,
        "failures": len(history) - successes,
        "last": history[-1],
    }


def reset_all() -> None:
    """Clear all replay history (for testing)."""
    _replay_log.clear()
