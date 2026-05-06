"""Unit tests for hookdrop/routing.py."""

import pytest
from unittest.mock import patch, MagicMock
from hookdrop import routing
from hookdrop.storage import RequestStore, WebhookRequest
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def reset_rules():
    routing.clear_rules()
    yield
    routing.clear_rules()


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, method="POST", path="/hook", body="hello"):
    req = WebhookRequest(
        id="abc123",
        method=method,
        path=path,
        headers={"Content-Type": "application/json"},
        body=body,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    store.save(req)
    return req


def test_add_and_list_rule():
    rule = routing.add_rule("my-rule", "http://example.com/hook")
    assert rule["name"] == "my-rule"
    assert rule["target_url"] == "http://example.com/hook"
    assert rule["enabled"] is True
    assert len(routing.list_rules()) == 1


def test_get_rule():
    routing.add_rule("r1", "http://a.com")
    assert routing.get_rule("r1")["name"] == "r1"
    assert routing.get_rule("missing") is None


def test_remove_rule():
    routing.add_rule("r1", "http://a.com")
    assert routing.remove_rule("r1") is True
    assert routing.list_rules() == []


def test_remove_rule_not_found():
    assert routing.remove_rule("ghost") is False


def test_enable_disable_rule():
    routing.add_rule("r1", "http://a.com")
    assert routing.disable_rule("r1") is True
    assert routing.get_rule("r1")["enabled"] is False
    assert routing.enable_rule("r1") is True
    assert routing.get_rule("r1")["enabled"] is True


def test_enable_disable_missing_rule():
    assert routing.enable_rule("nope") is False
    assert routing.disable_rule("nope") is False


def test_apply_rules_success(store):
    req = _make_request(store)
    routing.add_rule("fwd", "http://target.com/hook")
    mock_resp = MagicMock(status_code=200)
    with patch("hookdrop.routing.http_requests.request", return_value=mock_resp):
        results = routing.apply_rules(store, req.id)
    assert len(results) == 1
    assert results[0]["ok"] is True
    assert results[0]["status"] == 200


def test_apply_rules_skips_disabled(store):
    req = _make_request(store)
    routing.add_rule("fwd", "http://target.com/hook")
    routing.disable_rule("fwd")
    results = routing.apply_rules(store, req.id)
    assert results == []


def test_apply_rules_request_not_found(store):
    routing.add_rule("fwd", "http://target.com")
    results = routing.apply_rules(store, "nonexistent")
    assert results == []


def test_apply_rules_handles_exception(store):
    req = _make_request(store)
    routing.add_rule("fwd", "http://bad-host.invalid")
    with patch("hookdrop.routing.http_requests.request", side_effect=Exception("timeout")):
        results = routing.apply_rules(store, req.id)
    assert results[0]["ok"] is False
    assert "timeout" in results[0]["error"]
