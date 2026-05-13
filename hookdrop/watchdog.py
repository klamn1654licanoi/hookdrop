"""Watchdog module: monitor requests matching rules and trigger alerts on anomalies."""

import time
from typing import Dict, List, Optional

_watchdog_rules: Dict[str, dict] = {}
_watchdog_hits: Dict[str, List[float]] = {}


def add_watchdog_rule(name: str, method: Optional[str] = None, path_contains: Optional[str] = None,
                     max_per_minute: int = 60, min_per_minute: int = 0) -> dict:
    """Register a watchdog rule by name."""
    if not name:
        raise ValueError("Rule name must not be empty")
    if max_per_minute < 0 or min_per_minute < 0:
        raise ValueError("Rate limits must be non-negative")
    if min_per_minute > max_per_minute:
        raise ValueError("min_per_minute cannot exceed max_per_minute")
    rule = {
        "name": name,
        "method": method.upper() if method else None,
        "path_contains": path_contains,
        "max_per_minute": max_per_minute,
        "min_per_minute": min_per_minute,
    }
    _watchdog_rules[name] = rule
    _watchdog_hits.setdefault(name, [])
    return rule


def remove_watchdog_rule(name: str) -> bool:
    """Remove a watchdog rule. Returns True if removed, False if not found."""
    if name in _watchdog_rules:
        del _watchdog_rules[name]
        _watchdog_hits.pop(name, None)
        return True
    return False


def get_watchdog_rule(name: str) -> Optional[dict]:
    return _watchdog_rules.get(name)


def list_watchdog_rules() -> List[dict]:
    return list(_watchdog_rules.values())


def clear_watchdog_rules() -> None:
    _watchdog_rules.clear()
    _watchdog_hits.clear()


def record_hit(name: str) -> None:
    """Record a hit for a named watchdog rule at the current time."""
    if name not in _watchdog_hits:
        _watchdog_hits[name] = []
    _watchdog_hits[name].append(time.time())


def evaluate_rule(name: str) -> dict:
    """Evaluate a watchdog rule and return its current status."""
    rule = _watchdog_rules.get(name)
    if rule is None:
        raise KeyError(f"Watchdog rule '{name}' not found")
    now = time.time()
    window = [t for t in _watchdog_hits.get(name, []) if now - t <= 60]
    _watchdog_hits[name] = window
    rate = len(window)
    breached = rate > rule["max_per_minute"] or rate < rule["min_per_minute"]
    return {
        "name": name,
        "hits_last_minute": rate,
        "max_per_minute": rule["max_per_minute"],
        "min_per_minute": rule["min_per_minute"],
        "breached": breached,
    }


def evaluate_all() -> List[dict]:
    return [evaluate_rule(name) for name in _watchdog_rules]
