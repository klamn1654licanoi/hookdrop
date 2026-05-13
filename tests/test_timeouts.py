"""Unit tests for hookdrop.timeouts."""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import timeouts
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def reset():
    timeouts.clear_timeout_rules()
    yield
    timeouts.clear_timeout_rules()


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store: RequestStore, path: str = "/hook", duration: float = 1.0) -> WebhookRequest:
    req = WebhookRequest(
        method="POST",
        path=path,
        headers={},
        body="",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    req.duration = duration
    store.save(req)
    return req


def test_set_and_get_rule():
    timeouts.set_timeout_rule("/api", 2.5)
    assert timeouts.get_timeout_rule("/api") == 2.5


def test_set_invalid_rule_raises():
    with pytest.raises(ValueError):
        timeouts.set_timeout_rule("/api", -1)


def test_remove_existing_rule():
    timeouts.set_timeout_rule("/api", 1.0)
    assert timeouts.remove_timeout_rule("/api") is True
    assert timeouts.get_timeout_rule("/api") is None


def test_remove_missing_rule():
    assert timeouts.remove_timeout_rule("/missing") is False


def test_list_rules():
    timeouts.set_timeout_rule("/a", 1.0)
    timeouts.set_timeout_rule("/b", 2.0)
    rules = timeouts.list_timeout_rules()
    assert rules["/a"] == 1.0
    assert rules["/b"] == 2.0


def test_evaluate_timed_out(store):
    req = _make_request(store, path="/api/data", duration=5.0)
    timeouts.set_timeout_rule("/api", 2.0)
    assert timeouts.evaluate_request(store, req.id) is True


def test_evaluate_within_limit(store):
    req = _make_request(store, path="/api/data", duration=0.5)
    timeouts.set_timeout_rule("/api", 2.0)
    assert timeouts.evaluate_request(store, req.id) is False


def test_evaluate_no_matching_rule(store):
    req = _make_request(store, path="/other", duration=10.0)
    timeouts.set_timeout_rule("/api", 2.0)
    assert timeouts.evaluate_request(store, req.id) is None


def test_evaluate_missing_request(store):
    timeouts.set_timeout_rule("/api", 1.0)
    assert timeouts.evaluate_request(store, "nonexistent") is None


def test_is_timed_out_after_evaluate(store):
    req = _make_request(store, path="/hook", duration=3.0)
    timeouts.set_timeout_rule("/hook", 1.0)
    timeouts.evaluate_request(store, req.id)
    assert timeouts.is_timed_out(req.id) is True


def test_is_timed_out_before_evaluate():
    assert timeouts.is_timed_out("unknown-id") is None


def test_list_timed_out(store):
    r1 = _make_request(store, path="/api", duration=5.0)
    r2 = _make_request(store, path="/api", duration=0.1)
    timeouts.set_timeout_rule("/api", 2.0)
    flagged = timeouts.list_timed_out(store)
    ids = [f["id"] for f in flagged]
    assert r1.id in ids
    assert r2.id not in ids
