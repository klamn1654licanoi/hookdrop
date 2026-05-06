"""Request routing rules: match incoming webhooks and forward to target URLs."""

from typing import Optional
from hookdrop.storage import RequestStore
from hookdrop.filters import apply_filters
import requests as http_requests

_rules: list[dict] = []


def add_rule(name: str, target_url: str, filters: Optional[dict] = None) -> dict:
    """Add a routing rule. Returns the created rule."""
    rule = {
        "name": name,
        "target_url": target_url,
        "filters": filters or {},
        "enabled": True,
    }
    _rules.append(rule)
    return rule


def remove_rule(name: str) -> bool:
    """Remove a routing rule by name. Returns True if removed."""
    global _rules
    before = len(_rules)
    _rules = [r for r in _rules if r["name"] != name]
    return len(_rules) < before


def get_rule(name: str) -> Optional[dict]:
    """Retrieve a rule by name."""
    return next((r for r in _rules if r["name"] == name), None)


def list_rules() -> list[dict]:
    """Return all routing rules."""
    return list(_rules)


def clear_rules() -> None:
    """Remove all routing rules."""
    global _rules
    _rules = []


def enable_rule(name: str) -> bool:
    rule = get_rule(name)
    if rule is None:
        return False
    rule["enabled"] = True
    return True


def disable_rule(name: str) -> bool:
    rule = get_rule(name)
    if rule is None:
        return False
    rule["enabled"] = False
    return True


def apply_rules(store: RequestStore, request_id: str, timeout: int = 5) -> list[dict]:
    """Apply all matching enabled rules to the given request. Returns dispatch results."""
    req = store.get(request_id)
    if req is None:
        return []

    results = []
    for rule in _rules:
        if not rule["enabled"]:
            continue
        if not apply_filters(req, rule["filters"]):
            continue
        try:
            resp = http_requests.request(
                method=req.method,
                url=rule["target_url"],
                headers={k: v for k, v in req.headers.items() if k.lower() not in ("host", "content-length")},
                data=req.body,
                timeout=timeout,
            )
            results.append({"rule": rule["name"], "status": resp.status_code, "ok": True})
        except Exception as exc:
            results.append({"rule": rule["name"], "error": str(exc), "ok": False})
    return results
