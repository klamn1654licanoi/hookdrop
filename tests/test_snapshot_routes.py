"""Integration tests for snapshot HTTP routes."""

import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.snapshots import clear_all_snapshots


@pytest.fixture
def store():
    s = RequestStore()
    s.clear()
    return s


@pytest.fixture
def client(store):
    app = create_app(store)
    app.config["TESTING"] = True
    clear_all_snapshots()
    with app.test_client() as c:
        yield c
    clear_all_snapshots()


def _post_webhook(client, path="/hook", body=b'{"x": 1}'):
    return client.post(
        f"/webhook{path}",
        data=body,
        content_type="application/json",
    )


def test_list_snapshots_empty(client):
    resp = client.get("/snapshots")
    assert resp.status_code == 200
    assert resp.get_json()["snapshots"] == []


def test_save_and_list(client):
    _post_webhook(client)
    resp = client.post("/snapshots/mysnap")
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["snapshot"] == "mysnap"
    assert data["saved"] == 1
    resp2 = client.get("/snapshots")
    assert "mysnap" in resp2.get_json()["snapshots"]


def test_get_snapshot(client):
    _post_webhook(client, path="/test")
    client.post("/snapshots/getsnap")
    resp = client.get("/snapshots/getsnap")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 1
    assert data["requests"][0]["path"] == "/test"


def test_get_snapshot_not_found(client):
    resp = client.get("/snapshots/ghost")
    assert resp.status_code == 404


def test_restore_snapshot(client, store):
    _post_webhook(client, path="/original")
    client.post("/snapshots/restore_test")
    store.clear()
    resp = client.post("/snapshots/restore_test/restore")
    assert resp.status_code == 200
    assert resp.get_json()["restored"] == 1
    assert len(store.all()) == 1


def test_restore_not_found(client):
    resp = client.post("/snapshots/nope/restore")
    assert resp.status_code == 404


def test_delete_snapshot(client):
    client.post("/snapshots/delme")
    resp = client.delete("/snapshots/delme")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "delme"
    assert client.get("/snapshots/delme").status_code == 404


def test_delete_not_found(client):
    resp = client.delete("/snapshots/missing")
    assert resp.status_code == 404
