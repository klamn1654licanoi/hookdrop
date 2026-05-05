"""Tests for transform module and transform routes."""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.receiver import create_app
from hookdrop import transform
import datetime


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, path="/hook", method="POST", headers=None, body="hello"):
    req = WebhookRequest(
        id=None,
        method=method,
        path=path,
        headers=headers or {"Content-Type": "application/json"},
        body=body,
        timestamp=datetime.datetime.utcnow().isoformat(),
    )
    store.save(req)
    return req


@pytest.fixture
def client(store):
    app = create_app(store)
    from hookdrop.transform_routes import init_transform_routes
    init_transform_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def test_set_header_success(store):
    req = _make_request(store)
    result = transform.set_header(store, req.id, "X-Custom", "abc")
    assert result is not None
    assert result.headers["X-Custom"] == "abc"


def test_set_header_not_found(store):
    result = transform.set_header(store, "missing-id", "X-Custom", "abc")
    assert result is None


def test_remove_header_success(store):
    req = _make_request(store, headers={"X-Remove-Me": "yes"})
    result = transform.remove_header(store, req.id, "X-Remove-Me")
    assert result is not None
    assert "X-Remove-Me" not in result.headers


def test_remove_header_not_found(store):
    result = transform.remove_header(store, "bad-id", "X-Foo")
    assert result is None


def test_rewrite_body(store):
    req = _make_request(store, body="original")
    result = transform.rewrite_body(store, req.id, "new body")
    assert result.body == "new body"


def test_rewrite_path(store):
    req = _make_request(store, path="/old")
    result = transform.rewrite_path(store, req.id, "/new")
    assert result.path == "/new"


def test_route_get_transform(client, store):
    req = _make_request(store)
    resp = client.get(f"/requests/{req.id}/transform")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == req.id
    assert "headers" in data


def test_route_set_header(client, store):
    req = _make_request(store)
    resp = client.put(f"/requests/{req.id}/transform/header",
                      json={"key": "X-Test", "value": "val"})
    assert resp.status_code == 200
    assert resp.get_json()["headers"]["X-Test"] == "val"


def test_route_remove_header(client, store):
    req = _make_request(store, headers={"X-Drop": "yes"})
    resp = client.delete(f"/requests/{req.id}/transform/header",
                         json={"key": "X-Drop"})
    assert resp.status_code == 200
    assert "X-Drop" not in resp.get_json()["headers"]


def test_route_rewrite_body(client, store):
    req = _make_request(store)
    resp = client.put(f"/requests/{req.id}/transform/body",
                      json={"body": "updated"})
    assert resp.status_code == 200
    assert resp.get_json()["body"] == "updated"


def test_route_rewrite_path(client, store):
    req = _make_request(store)
    resp = client.put(f"/requests/{req.id}/transform/path",
                      json={"path": "/changed"})
    assert resp.status_code == 200
    assert resp.get_json()["path"] == "/changed"


def test_route_not_found(client):
    resp = client.get("/requests/nonexistent/transform")
    assert resp.status_code == 404
