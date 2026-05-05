from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

from hookdrop.storage import RequestStore


def requests_in_window(
    store: RequestStore, window_seconds: int = 60
) -> List[dict]:
    """Return requests received within the last `window_seconds`."""
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    results = []
    for req in store.all():
        try:
            ts = datetime.fromisoformat(req.timestamp)
        except (AttributeError, ValueError):
            continue
        if ts >= cutoff:
            results.append(req)
    return results


def rate_per_minute(store: RequestStore) -> float:
    """Compute requests per minute based on the last 60 seconds."""
    recent = requests_in_window(store, window_seconds=60)
    return float(len(recent))


def rate_by_method(store: RequestStore, window_seconds: int = 60) -> Dict[str, int]:
    """Return request counts grouped by HTTP method within the window."""
    recent = requests_in_window(store, window_seconds=window_seconds)
    counts: Dict[str, int] = defaultdict(int)
    for req in recent:
        counts[req.method.upper()] += 1
    return dict(counts)


def rate_by_path(store: RequestStore, window_seconds: int = 60) -> Dict[str, int]:
    """Return request counts grouped by path within the window."""
    recent = requests_in_window(store, window_seconds=window_seconds)
    counts: Dict[str, int] = defaultdict(int)
    for req in recent:
        counts[req.path] += 1
    return dict(counts)


def rate_summary(store: RequestStore, window_seconds: int = 60) -> dict:
    """Return a full rate summary for the given time window."""
    recent = requests_in_window(store, window_seconds=window_seconds)
    return {
        "window_seconds": window_seconds,
        "total": len(recent),
        "per_minute": round(len(recent) * (60 / window_seconds), 2),
        "by_method": rate_by_method(store, window_seconds),
        "by_path": rate_by_path(store, window_seconds),
    }
