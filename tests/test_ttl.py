"""Tests for hookdrop/ttl.py"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.ttl import (
    is_expired,
    expire_requests,
    get_expiry_time,
    seconds_until_expiry,
    ttl_summary,
)


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, age_seconds=0, path="/webhook"):
    req = WebhookRequest(
        method="POST",
        path=path,
        headers={},
        body="",
        timestamp=datetime.utcnow() - timedelta(seconds=age_seconds),
    )
    store.save(req)
    return req


def test_is_expired_old_request():
    req = WebhookRequest(
        method="POST", path="/", headers={}, body="",
        timestamp=datetime.utcnow() - timedelta(seconds=200),
    )
    assert is_expired(req, ttl_seconds=100) is True


def test_is_expired_fresh_request():
    req = WebhookRequest(
        method="POST", path="/", headers={}, body="",
        timestamp=datetime.utcnow() - timedelta(seconds=10),
    )
    assert is_expired(req, ttl_seconds=100) is False


def test_expire_requests_removes_old(store):
    old = _make_request(store, age_seconds=500)
    fresh = _make_request(store, age_seconds=10)
    removed = expire_requests(store, ttl_seconds=100)
    assert old.id in removed
    assert fresh.id not in removed
    assert store.get(old.id) is None
    assert store.get(fresh.id) is not None


def test_expire_requests_empty_store(store):
    removed = expire_requests(store, ttl_seconds=60)
    assert removed == []


def test_expire_requests_none_expired(store):
    _make_request(store, age_seconds=5)
    _make_request(store, age_seconds=10)
    removed = expire_requests(store, ttl_seconds=3600)
    assert removed == []


def test_get_expiry_time():
    ts = datetime(2024, 1, 1, 12, 0, 0)
    req = WebhookRequest(method="GET", path="/", headers={}, body="", timestamp=ts)
    expiry = get_expiry_time(req, ttl_seconds=3600)
    assert expiry == datetime(2024, 1, 1, 13, 0, 0)


def test_seconds_until_expiry_positive():
    req = WebhookRequest(
        method="GET", path="/", headers={}, body="",
        timestamp=datetime.utcnow() - timedelta(seconds=30),
    )
    remaining = seconds_until_expiry(req, ttl_seconds=3600)
    assert 3500 < remaining < 3600


def test_seconds_until_expiry_negative():
    req = WebhookRequest(
        method="GET", path="/", headers={}, body="",
        timestamp=datetime.utcnow() - timedelta(seconds=200),
    )
    remaining = seconds_until_expiry(req, ttl_seconds=100)
    assert remaining < 0


def test_ttl_summary_empty(store):
    result = ttl_summary(store, ttl_seconds=60)
    assert result == {"total": 0, "active": 0, "expired": 0, "ttl_seconds": 60}


def test_ttl_summary_mixed(store):
    _make_request(store, age_seconds=200)
    _make_request(store, age_seconds=10)
    _make_request(store, age_seconds=5)
    result = ttl_summary(store, ttl_seconds=100)
    assert result["total"] == 3
    assert result["expired"] == 1
    assert result["active"] == 2
    assert result["ttl_seconds"] == 100
