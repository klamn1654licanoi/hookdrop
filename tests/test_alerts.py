import pytest
from hookdrop import alerts
from hookdrop.storage import RequestStore, WebhookRequest
from datetime import datetime


@pytest.fixture(autouse=True)
def reset_alerts():
    alerts.clear_alerts()
    yield
    alerts.clear_alerts()


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, method="POST", path="/hook", headers=None, body="", response_status=200):
    req = WebhookRequest(
        id=None,
        method=method,
        path=path,
        headers=headers or {},
        body=body,
        timestamp=datetime.utcnow(),
        response_status=response_status,
    )
    store.save(req)
    return req


def test_add_and_list_alert():
    rule = alerts.add_alert("on_post", "method", "POST")
    assert rule["name"] == "on_post"
    assert len(alerts.list_alerts()) == 1


def test_get_alert():
    alerts.add_alert("on_get", "method", "GET")
    rule = alerts.get_alert("on_get")
    assert rule is not None
    assert rule["condition"] == "method"


def test_get_alert_not_found():
    assert alerts.get_alert("missing") is None


def test_remove_alert():
    alerts.add_alert("to_remove", "method", "DELETE")
    removed = alerts.remove_alert("to_remove")
    assert removed is True
    assert alerts.get_alert("to_remove") is None


def test_remove_alert_not_found():
    assert alerts.remove_alert("ghost") is False


def test_evaluate_method_match(store):
    alerts.add_alert("on_post", "method", "POST")
    req = _make_request(store, method="POST")
    triggered = alerts.evaluate_alerts(req)
    assert len(triggered) == 1
    assert triggered[0]["name"] == "on_post"


def test_evaluate_method_no_match(store):
    alerts.add_alert("on_delete", "method", "DELETE")
    req = _make_request(store, method="GET")
    triggered = alerts.evaluate_alerts(req)
    assert triggered == []


def test_evaluate_path_contains(store):
    alerts.add_alert("payment", "path_contains", "payment")
    req = _make_request(store, path="/api/payment/confirm")
    triggered = alerts.evaluate_alerts(req)
    assert any(r["name"] == "payment" for r in triggered)


def test_evaluate_status_gte(store):
    alerts.add_alert("errors", "status_gte", "400")
    req = _make_request(store, response_status=500)
    triggered = alerts.evaluate_alerts(req)
    assert any(r["name"] == "errors" for r in triggered)


def test_evaluate_status_gte_below_threshold(store):
    alerts.add_alert("errors", "status_gte", "400")
    req = _make_request(store, response_status=200)
    triggered = alerts.evaluate_alerts(req)
    assert triggered == []


def test_evaluate_header_present(store):
    alerts.add_alert("has_auth", "header_present", "Authorization")
    req = _make_request(store, headers={"Authorization": "Bearer token"})
    triggered = alerts.evaluate_alerts(req)
    assert any(r["name"] == "has_auth" for r in triggered)


def test_scan_store(store):
    alerts.add_alert("on_post", "method", "POST")
    _make_request(store, method="POST")
    _make_request(store, method="POST")
    _make_request(store, method="GET")
    results = alerts.scan_store(store)
    assert len(results["on_post"]) == 2
