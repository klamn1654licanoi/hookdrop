from collections import Counter
from typing import Dict, Any
from hookdrop.storage import RequestStore


def compute_stats(store: RequestStore) -> Dict[str, Any]:
    """Compute summary statistics over all stored webhook requests."""
    requests = store.all()

    if not requests:
        return {
            "total": 0,
            "by_method": {},
            "by_path": {},
            "by_status": {},
        }

    method_counts = Counter(r.method.upper() for r in requests)
    path_counts = Counter(r.path for r in requests)
    status_counts = Counter(str(r.status_code) for r in requests if r.status_code is not None)

    return {
        "total": len(requests),
        "by_method": dict(method_counts),
        "by_path": dict(path_counts),
        "by_status": dict(status_counts),
    }


def most_common_method(store: RequestStore) -> str | None:
    """Return the most frequently used HTTP method, or None if no requests."""
    requests = store.all()
    if not requests:
        return None
    counts = Counter(r.method.upper() for r in requests)
    return counts.most_common(1)[0][0]


def most_common_path(store: RequestStore) -> str | None:
    """Return the most frequently hit path, or None if no requests."""
    requests = store.all()
    if not requests:
        return None
    counts = Counter(r.path for r in requests)
    return counts.most_common(1)[0][0]


def error_rate(store: RequestStore) -> float | None:
    """Return the fraction of requests with a 4xx or 5xx status code.

    Returns None if no requests have a recorded status code.
    Returns a float between 0.0 and 1.0 otherwise.
    """
    requests = [r for r in store.all() if r.status_code is not None]
    if not requests:
        return None
    error_count = sum(1 for r in requests if r.status_code >= 400)
    return error_count / len(requests)
