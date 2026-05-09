"""Unit tests for hookdrop.throttle."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
from hookdrop.storage import WebhookRequest
import hookdrop.throttle as thr


@pytest.fixture(autouse=True)
def reset_rules():
    thr.clear_throttle_rules()
    yield
    thr.clear_throttle_rules()


def _make_store(*paths, age_seconds=0):
    store = MagicMock()
    requests = [
        WebhookRequest(
            id=str(i),
            method="POST",
            path=p,
            headers={},
            body="",
            timestamp=datetime.utcnow() - timedelta(seconds=age_seconds),
        )
        for i, p in enumerate(paths)
    ]
    store.get_all.return_value = requests
    return store


def test_set_and_get_rule():
    thr.set_throttle_rule("/hook", 5, 60)
    assert thr.get_throttle_rule("/hook") == (5, 60)


def test_get_rule_not_found():
    assert thr.get_throttle_rule("/missing") is None


def test_set_invalid_max_requests():
    with pytest.raises(ValueError):
        thr.set_throttle_rule("/hook", 0, 60)


def test_set_invalid_window():
    with pytest.raises(ValueError):
        thr.set_throttle_rule("/hook", 5, 0)


def test_remove_rule_existing():
    thr.set_throttle_rule("/hook", 5, 60)
    assert thr.remove_throttle_rule("/hook") is True
    assert thr.get_throttle_rule("/hook") is None


def test_remove_rule_missing():
    assert thr.remove_throttle_rule("/nope") is False


def test_list_rules():
    thr.set_throttle_rule("/a", 3, 30)
    thr.set_throttle_rule("/b", 10, 120)
    rules = thr.list_throttle_rules()
    assert rules["/a"] == {"max_requests": 3, "window_seconds": 30}
    assert rules["/b"] == {"max_requests": 10, "window_seconds": 120}


def test_is_throttled_no_rule():
    store = _make_store("/hook", "/hook")
    assert thr.is_throttled(store, "/hook") is False


def test_is_throttled_under_limit():
    thr.set_throttle_rule("/hook", 5, 60)
    store = _make_store("/hook", "/hook")
    assert thr.is_throttled(store, "/hook") is False


def test_is_throttled_at_limit():
    thr.set_throttle_rule("/hook", 2, 60)
    store = _make_store("/hook", "/hook")
    assert thr.is_throttled(store, "/hook") is True


def test_is_throttled_old_requests_excluded():
    thr.set_throttle_rule("/hook", 2, 60)
    store = _make_store("/hook", "/hook", age_seconds=120)
    assert thr.is_throttled(store, "/hook") is False


def test_throttle_summary():
    thr.set_throttle_rule("/hook", 3, 60)
    store = _make_store("/hook", "/hook")
    result = thr.throttle_summary(store)
    assert len(result) == 1
    entry = result[0]
    assert entry["key"] == "/hook"
    assert entry["current_count"] == 2
    assert entry["throttled"] is False
