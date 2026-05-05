import pytest
from flask import Flask
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.bookmark_routes import init_bookmark_routes
import hookdrop.bookmarks as bookmarks_module
import time


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_bookmark_routes(app, store)
    # also register receiver to post webhooks
    from hookdrop.receiver import init_routes
    init_routes(app, store)
    bookmarks_module.clear_bookmarks()
    with app.test_client() as c:
        yield c
    bookmarks_module.clear_bookmarks()


def _post_webhook(client):
    resp = client.post("/hook", json={"event": "test"}, headers={"X-Event": "ping"})
    assert resp.status_code == 200
    return resp.get_json()["id"]


def test_list_bookmarks_empty(client):
    resp = client.get("/bookmarks")
    assert resp.status_code == 200
    assert resp.get_json() == {}


def test_add_and_get_bookmark(client):
    req_id = _post_webhook(client)
    resp = client.put("/bookmarks/my-label", json={"request_id": req_id})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["label"] == "my-label"
    assert data["request_id"] == req_id

    resp = client.get("/bookmarks/my-label")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == req_id


def test_add_bookmark_not_found(client):
    resp = client.put("/bookmarks/ghost", json={"request_id": "nonexistent-id"})
    assert resp.status_code == 404


def test_add_bookmark_missing_request_id(client):
    resp = client.put("/bookmarks/bad", json={})
    assert resp.status_code == 400


def test_get_bookmark_not_found(client):
    resp = client.get("/bookmarks/missing")
    assert resp.status_code == 404


def test_remove_bookmark(client):
    req_id = _post_webhook(client)
    client.put("/bookmarks/to-delete", json={"request_id": req_id})
    resp = client.delete("/bookmarks/to-delete")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "to-delete"

    resp = client.get("/bookmarks/to-delete")
    assert resp.status_code == 404


def test_remove_bookmark_not_found(client):
    resp = client.delete("/bookmarks/nope")
    assert resp.status_code == 404


def test_list_bookmarks_after_adding(client):
    req_id = _post_webhook(client)
    client.put("/bookmarks/alpha", json={"request_id": req_id})
    client.put("/bookmarks/beta", json={"request_id": req_id})
    resp = client.get("/bookmarks")
    data = resp.get_json()
    assert "alpha" in data
    assert "beta" in data
    assert data["alpha"] == req_id
    assert data["beta"] == req_id
