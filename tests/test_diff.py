"""Unit tests for hookdrop/diff.py"""

import pytest
from hookdrop.storage import WebhookRequest
from hookdrop.diff import diff_headers, diff_body, diff_requests


def _make_request(**kwargs) -> WebhookRequest:
    defaults = {
        "id": "abc",
        "method": "POST",
        "path": "/webhook",
        "headers": {"content-type": "application/json"},
        "body": '{"key": "value"}',
        "timestamp": "2024-01-01T00:00:00",
    }
    defaults.update(kwargs)
    return WebhookRequest(**defaults)


def test_diff_headers_no_change():
    a = _make_request(headers={"content-type": "application/json"})
    b = _make_request(headers={"content-type": "application/json"})
    result = diff_headers(a, b)
    assert result["added"] == {}
    assert result["removed"] == {}
    assert result["changed"] == {}


def test_diff_headers_added():
    a = _make_request(headers={"content-type": "application/json"})
    b = _make_request(headers={"content-type": "application/json", "x-token": "abc"})
    result = diff_headers(a, b)
    assert "x-token" in result["added"]
    assert result["added"]["x-token"] == "abc"


def test_diff_headers_removed():
    a = _make_request(headers={"content-type": "application/json", "x-token": "abc"})
    b = _make_request(headers={"content-type": "application/json"})
    result = diff_headers(a, b)
    assert "x-token" in result["removed"]


def test_diff_headers_changed():
    a = _make_request(headers={"content-type": "application/json"})
    b = _make_request(headers={"content-type": "text/plain"})
    result = diff_headers(a, b)
    assert "content-type" in result["changed"]
    assert result["changed"]["content-type"]["from"] == "application/json"
    assert result["changed"]["content-type"]["to"] == "text/plain"


def test_diff_body_unchanged():
    a = _make_request(body="hello")
    b = _make_request(body="hello")
    result = diff_body(a, b)
    assert result["changed"] is False


def test_diff_body_changed():
    a = _make_request(body="hello")
    b = _make_request(body="world")
    result = diff_body(a, b)
    assert result["changed"] is True
    assert result["from"] == "hello"
    assert result["to"] == "world"


def test_diff_requests_full():
    a = _make_request(id="req-1", method="POST", path="/a", body="foo")
    b = _make_request(id="req-2", method="GET", path="/b", body="bar")
    result = diff_requests(a, b)
    assert result["id_a"] == "req-1"
    assert result["id_b"] == "req-2"
    assert result["method"]["changed"] is True
    assert result["path"]["changed"] is True
    assert result["body"]["changed"] is True


def test_diff_requests_no_change():
    a = _make_request(id="req-1")
    b = _make_request(id="req-2")
    result = diff_requests(a, b)
    assert result["method"]["changed"] is False
    assert result["path"]["changed"] is False
    assert result["body"]["changed"] is False
