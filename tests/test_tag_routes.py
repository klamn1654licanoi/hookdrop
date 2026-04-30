"""Integration tests for tag routes."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import init_receiver
from hookdrop.tag_routes import init_tag_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_receiver(app, store)
    init_tag_routes(app, store)
    with app.test_client() as c:
        yield c


def _post_webhook(client):
    resp = client.post("/hook/test", data="hello", content_type="text/plain")
    assert resp.status_code == 200
    return resp.get_json()["id"]


def test_list_tags_empty(client):
    req_id = _post_webhook(client)
    resp = client.get(f"/requests/{req_id}/tags")
    assert resp.status_code == 200
    assert resp.get_json()["tags"] == []


def test_add_tag(client):
    req_id = _post_webhook(client)
    resp = client.post(f"/requests/{req_id}/tags", json={"tag": "urgent"})
    assert resp.status_code == 200
    assert "urgent" in resp.get_json()["tags"]


def test_add_tag_missing_field(client):
    req_id = _post_webhook(client)
    resp = client.post(f"/requests/{req_id}/tags", json={})
    assert resp.status_code == 400


def test_add_tag_not_found(client):
    resp = client.post("/requests/ghost/tags", json={"tag": "x"})
    assert resp.status_code == 404


def test_remove_tag(client):
    req_id = _post_webhook(client)
    client.post(f"/requests/{req_id}/tags", json={"tag": "delete-me"})
    resp = client.delete(f"/requests/{req_id}/tags/delete-me")
    assert resp.status_code == 200
    assert "delete-me" not in resp.get_json()["tags"]


def test_remove_tag_not_found(client):
    resp = client.delete("/requests/ghost/tags/sometag")
    assert resp.status_code == 404


def test_all_tags(client):
    r1 = _post_webhook(client)
    r2 = _post_webhook(client)
    client.post(f"/requests/{r1}/tags", json={"tag": "beta"})
    client.post(f"/requests/{r2}/tags", json={"tag": "alpha"})
    resp = client.get("/tags")
    assert resp.status_code == 200
    assert resp.get_json()["tags"] == ["alpha", "beta"]


def test_requests_by_tag(client):
    r1 = _post_webhook(client)
    _post_webhook(client)
    client.post(f"/requests/{r1}/tags", json={"tag": "special"})
    resp = client.get("/tags/special/requests")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 1
    assert data[0]["id"] == r1
