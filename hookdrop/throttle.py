"""Request throttle/rate-limiting detection and enforcement for incoming webhooks."""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# throttle_rules: key -> (max_requests, window_seconds)
_throttle_rules: Dict[str, Tuple[int, int]] = {}


def set_throttle_rule(key: str, max_requests: int, window_seconds: int) -> None:
    """Define a throttle rule by key (e.g. path or method)."""
    if max_requests < 1:
        raise ValueError("max_requests must be >= 1")
    if window_seconds < 1:
        raise ValueError("window_seconds must be >= 1")
    _throttle_rules[key] = (max_requests, window_seconds)


def get_throttle_rule(key: str) -> Optional[Tuple[int, int]]:
    """Return the throttle rule for a key, or None."""
    return _throttle_rules.get(key)


def remove_throttle_rule(key: str) -> bool:
    """Remove a throttle rule. Returns True if it existed."""
    if key in _throttle_rules:
        del _throttle_rules[key]
        return True
    return False


def list_throttle_rules() -> Dict[str, Dict]:
    """Return all throttle rules as serialisable dicts."""
    return {
        k: {"max_requests": v[0], "window_seconds": v[1]}
        for k, v in _throttle_rules.items()
    }


def clear_throttle_rules() -> None:
    """Remove all throttle rules."""
    _throttle_rules.clear()


def is_throttled(store, key: str) -> bool:
    """Check whether requests matching *key* exceed the defined throttle rule.

    *key* is matched against each request's path.  Returns False when no rule
    exists for the key.
    """
    rule = _throttle_rules.get(key)
    if rule is None:
        return False
    max_requests, window_seconds = rule
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    matching = [
        r for r in store.get_all()
        if r.path == key and r.timestamp >= cutoff
    ]
    return len(matching) >= max_requests


def throttle_summary(store, window_seconds: int = 60) -> List[Dict]:
    """Return per-key counts vs. limits for all defined rules."""
    cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
    summary = []
    for key, (max_req, win_sec) in _throttle_rules.items():
        win_cutoff = datetime.utcnow() - timedelta(seconds=win_sec)
        count = sum(
            1 for r in store.get_all()
            if r.path == key and r.timestamp >= win_cutoff
        )
        summary.append({
            "key": key,
            "max_requests": max_req,
            "window_seconds": win_sec,
            "current_count": count,
            "throttled": count >= max_req,
        })
    return summary
