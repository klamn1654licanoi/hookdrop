"""Tests for the webhook receiver and in-memory storage."""

import pytest
from fastapi.testclient import TestClient

from hookdrop.receiver import app, store


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()
    yield
    store.clear()


client = TestClient(app)


def test_receive_webhook_post():
    resp = client.post("/hook/github/push", json={"ref": "main"},
                       headers={"X-GitHub-Event": "push"})
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert data["status"] == "received"


def test_receive_webhook_get():
    resp = client.get("/hook/ping?foo=bar")
    assert resp.status_code == 200


def test_list_requests_empty():
    resp = client.get("/inspect")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_requests_after_receive():
    client.post("/hook/test", content=b"hello")
    client.post("/hook/test", content=b"world")
    resp = client.get("/inspect")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 2
    # Newest first
    assert items[0]["body"] == "world"


def test_get_single_request():
    post_resp = client.post("/hook/single", content=b"payload")
    req_id = post_resp.json()["id"]
    resp = client.get(f"/inspect/{req_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == req_id
    assert data["body"] == "payload"
    assert data["path"] == "/single"


def test_get_missing_request():
    resp = client.get("/inspect/nonexistent-id")
    assert resp.status_code == 404


def test_delete_request():
    post_resp = client.post("/hook/del", content=b"bye")
    req_id = post_resp.json()["id"]
    del_resp = client.delete(f"/inspect/{req_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] == req_id
    assert client.get(f"/inspect/{req_id}").status_code == 404


def test_delete_missing_request():
    """Deleting a non-existent request should return 404."""
    resp = client.delete("/inspect/nonexistent-id")
    assert resp.status_code == 404


def test_clear_all_requests():
    client.post("/hook/a")
    client.post("/hook/b")
    resp = client.delete("/inspect")
    assert resp.status_code == 200
    assert resp.json()["cleared"] == 2
    assert client.get("/inspect").json() == []
