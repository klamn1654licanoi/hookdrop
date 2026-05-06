from typing import Optional, Callable, Dict, List
from hookdrop.storage import RequestStore, WebhookRequest

_alert_rules: Dict[str, dict] = {}


def add_alert(name: str, condition: str, value: str, notify: Optional[str] = None) -> dict:
    """Register an alert rule. condition: 'method', 'path_contains', 'status_gte'."""
    rule = {"name": name, "condition": condition, "value": value, "notify": notify}
    _alert_rules[name] = rule
    return rule


def remove_alert(name: str) -> bool:
    if name in _alert_rules:
        del _alert_rules[name]
        return True
    return False


def get_alert(name: str) -> Optional[dict]:
    return _alert_rules.get(name)


def list_alerts() -> List[dict]:
    return list(_alert_rules.values())


def clear_alerts() -> None:
    _alert_rules.clear()


def _request_matches_alert(req: WebhookRequest, rule: dict) -> bool:
    condition = rule["condition"]
    value = rule["value"]
    if condition == "method":
        return req.method.upper() == value.upper()
    elif condition == "path_contains":
        return value.lower() in req.path.lower()
    elif condition == "status_gte":
        try:
            return (req.response_status or 0) >= int(value)
        except (ValueError, TypeError):
            return False
    elif condition == "header_present":
        return value.lower() in {k.lower() for k in req.headers.keys()}
    return False


def evaluate_alerts(req: WebhookRequest) -> List[dict]:
    """Return list of triggered alert rules for a given request."""
    triggered = []
    for rule in _alert_rules.values():
        if _request_matches_alert(req, rule):
            triggered.append(rule)
    return triggered


def scan_store(store: RequestStore) -> Dict[str, List[str]]:
    """Scan all stored requests and return {alert_name: [request_ids]}."""
    results: Dict[str, List[str]] = {name: [] for name in _alert_rules}
    for req in store.all():
        for rule in _alert_rules.values():
            if _request_matches_alert(req, rule):
                results[rule["name"]].append(req.id)
    return results
