import pytest
from datetime import datetime, timedelta

from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.rate import (
    requests_in_window,
    rate_per_minute,
    rate_by_method,
    rate_by_path,
    rate_summary,
)


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, method="POST", path="/hook", seconds_ago=5):
    ts = (datetime.utcnow() - timedelta(seconds=seconds_ago)).isoformat()
    req = WebhookRequest(
        id=store._next_id(),
        method=method,
        path=path,
        headers={},
        body="",
        timestamp=ts,
    )
    store.save(req)
    return req


def test_requests_in_window_empty(store):
    assert requests_in_window(store, 60) == []


def test_requests_in_window_recent(store):
    _make_request(store, seconds_ago=10)
    result = requests_in_window(store, window_seconds=60)
    assert len(result) == 1


def test_requests_in_window_excludes_old(store):
    _make_request(store, seconds_ago=120)
    result = requests_in_window(store, window_seconds=60)
    assert len(result) == 0


def test_rate_per_minute_empty(store):
    assert rate_per_minute(store) == 0.0


def test_rate_per_minute_counts_recent(store):
    _make_request(store, seconds_ago=5)
    _make_request(store, seconds_ago=15)
    assert rate_per_minute(store) == 2.0


def test_rate_by_method(store):
    _make_request(store, method="POST", seconds_ago=5)
    _make_request(store, method="GET", seconds_ago=5)
    _make_request(store, method="POST", seconds_ago=5)
    result = rate_by_method(store, window_seconds=60)
    assert result["POST"] == 2
    assert result["GET"] == 1


def test_rate_by_path(store):
    _make_request(store, path="/a", seconds_ago=5)
    _make_request(store, path="/b", seconds_ago=5)
    _make_request(store, path="/a", seconds_ago=5)
    result = rate_by_path(store, window_seconds=60)
    assert result["/a"] == 2
    assert result["/b"] == 1


def test_rate_summary_structure(store):
    _make_request(store, method="POST", path="/hook", seconds_ago=5)
    summary = rate_summary(store, window_seconds=60)
    assert summary["window_seconds"] == 60
    assert summary["total"] == 1
    assert "per_minute" in summary
    assert "by_method" in summary
    assert "by_path" in summary


def test_rate_summary_per_minute_scaling(store):
    _make_request(store, seconds_ago=5)
    summary = rate_summary(store, window_seconds=30)
    # 1 request in 30s => 2 per minute
    assert summary["per_minute"] == 2.0
