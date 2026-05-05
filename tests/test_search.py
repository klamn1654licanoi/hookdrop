import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.search import search_requests, search_by_header_value
import datetime


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, method="POST", path="/webhook", headers=None, body=""):
    req = WebhookRequest(
        id=f"req-{len(store.all())}",
        method=method,
        path=path,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
        timestamp=datetime.datetime.utcnow().isoformat(),
    )
    store.save(req)
    return req


def test_search_by_method(store):
    _make_request(store, method="POST")
    _make_request(store, method="GET")
    results = search_requests(store, "get", fields=["method"])
    assert len(results) == 1
    assert results[0].method == "GET"


def test_search_by_path(store):
    _make_request(store, path="/orders")
    _make_request(store, path="/users")
    results = search_requests(store, "orders", fields=["path"])
    assert len(results) == 1
    assert results[0].path == "/orders"


def test_search_by_body(store):
    _make_request(store, body='{"event": "payment.success"}')
    _make_request(store, body='{"event": "user.created"}')
    results = search_requests(store, "payment", fields=["body"])
    assert len(results) == 1
    assert "payment" in results[0].body


def test_search_by_header(store):
    _make_request(store, headers={"X-Source": "stripe"})
    _make_request(store, headers={"X-Source": "github"})
    results = search_requests(store, "stripe", fields=["headers"])
    assert len(results) == 1


def test_search_default_fields(store):
    _make_request(store, path="/ping", body="hello world")
    _make_request(store, path="/other", body="nothing here")
    results = search_requests(store, "hello")
    assert len(results) == 1


def test_search_no_match(store):
    _make_request(store, path="/test", body="some content")
    results = search_requests(store, "zzznomatch")
    assert results == []


def test_search_empty_store(store):
    results = search_requests(store, "anything")
    assert results == []


def test_search_case_insensitive(store):
    _make_request(store, path="/WebHook")
    results = search_requests(store, "webhook", fields=["path"])
    assert len(results) == 1


def test_search_by_header_value(store):
    _make_request(store, headers={"Authorization": "Bearer token123"})
    _make_request(store, headers={"Authorization": "Basic abc"})
    results = search_by_header_value(store, "authorization", "bearer")
    assert len(results) == 1
    assert "Bearer" in results[0].headers.get("Authorization", "")


def test_search_by_header_value_not_found(store):
    _make_request(store, headers={"X-Custom": "foo"})
    results = search_by_header_value(store, "X-Custom", "bar")
    assert results == []
