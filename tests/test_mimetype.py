"""Tests for hookdrop.mimetype module."""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import mimetype as mt_module
from hookdrop.mimetype import (
    detect_mimetype,
    set_mimetype_override,
    get_mimetype_override,
    remove_mimetype_override,
    clear_mimetype_overrides,
    effective_mimetype,
    filter_by_mimetype,
    is_json,
    is_form,
    mimetype_summary,
)


@pytest.fixture(autouse=True)
def reset_overrides():
    clear_mimetype_overrides()
    yield
    clear_mimetype_overrides()


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, request_id="req-1", method="POST", path="/hook",
                  headers=None, body="", status=200):
    req = WebhookRequest(
        id=request_id,
        method=method,
        path=path,
        headers=headers or {},
        body=body,
        status_code=status,
    )
    store.save(req)
    return req


def test_detect_mimetype_json():
    req = _make_request(
        RequestStore(), headers={"content-type": "application/json"}, body='{"k":1}'
    )
    assert detect_mimetype(req) == "application/json"


def test_detect_mimetype_with_charset():
    req = _make_request(
        RequestStore(),
        headers={"content-type": "application/json; charset=utf-8"},
    )
    assert detect_mimetype(req) == "application/json"


def test_detect_mimetype_missing_header():
    req = _make_request(RequestStore(), headers={})
    assert detect_mimetype(req) == "application/octet-stream"


def test_set_and_get_override():
    set_mimetype_override("req-99", "text/plain")
    assert get_mimetype_override("req-99") == "text/plain"


def test_remove_override_existing():
    set_mimetype_override("req-1", "text/xml")
    result = remove_mimetype_override("req-1")
    assert result is True
    assert get_mimetype_override("req-1") is None


def test_remove_override_missing():
    result = remove_mimetype_override("nonexistent")
    assert result is False


def test_effective_mimetype_uses_override():
    req = _make_request(
        RequestStore(), headers={"content-type": "application/json"}
    )
    set_mimetype_override(req.id, "text/plain")
    assert effective_mimetype(req) == "text/plain"


def test_effective_mimetype_falls_back_to_detected():
    req = _make_request(
        RequestStore(), headers={"content-type": "application/xml"}
    )
    assert effective_mimetype(req) == "application/xml"


def test_filter_by_mimetype():
    store = RequestStore()
    r1 = _make_request(store, "a", headers={"content-type": "application/json"})
    r2 = _make_request(store, "b", headers={"content-type": "text/plain"})
    r3 = _make_request(store, "c", headers={"content-type": "application/json"})
    result = filter_by_mimetype([r1, r2, r3], "json")
    assert len(result) == 2
    assert r2 not in result


def test_is_json_valid():
    req = _make_request(
        RequestStore(),
        headers={"content-type": "application/json"},
        body='{"hello": "world"}',
    )
    assert is_json(req) is True


def test_is_json_invalid_body():
    req = _make_request(
        RequestStore(),
        headers={"content-type": "application/json"},
        body="not-json",
    )
    assert is_json(req) is False


def test_is_form():
    req = _make_request(
        RequestStore(),
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert is_form(req) is True


def test_mimetype_summary():
    store = RequestStore()
    r1 = _make_request(store, "a", headers={"content-type": "application/json"})
    r2 = _make_request(store, "b", headers={"content-type": "text/plain"})
    r3 = _make_request(store, "c", headers={"content-type": "application/json"})
    summary = mimetype_summary([r1, r2, r3])
    assert summary["application/json"] == 2
    assert summary["text/plain"] == 1
