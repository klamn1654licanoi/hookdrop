"""Tests for request deduplication (dedup.py and dedup_routes.py)."""

import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop import dedup
from hookdrop.dedup_routes import init_dedup_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_dedup_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def reset(store):
    store.clear()
    dedup.clear_dedup()
    yield
    store.clear()
    dedup.clear_dedup()


def _post_webhook(client, path="/hook", body=b"hello", headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    resp = client.post(path, data=body, headers=h)
    return resp.get_json()["id"]


def test_register_request(store, client):
    rid = _post_webhook(client)
    resp = client.post(f"/dedup/register/{rid}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["request_id"] == rid
    assert "fingerprint" in data
    assert len(data["fingerprint"]) == 64  # sha256 hex


def test_register_not_found(client):
    resp = client.post("/dedup/register/nonexistent")
    assert resp.status_code == 404


def test_check_not_duplicate(store, client):
    rid = _post_webhook(client)
    client.post(f"/dedup/register/{rid}")
    resp = client.get(f"/dedup/check/{rid}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_duplicate"] is False
    assert data["duplicates"] == []


def test_check_is_duplicate(store, client):
    rid1 = _post_webhook(client, body=b"same")
    rid2 = _post_webhook(client, body=b"same")
    client.post(f"/dedup/register/{rid1}")
    client.post(f"/dedup/register/{rid2}")
    resp = client.get(f"/dedup/check/{rid1}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["is_duplicate"] is True
    assert rid2 in data["duplicates"]


def test_get_duplicates_route(store, client):
    rid1 = _post_webhook(client, body=b"dup")
    rid2 = _post_webhook(client, body=b"dup")
    client.post(f"/dedup/register/{rid1}")
    client.post(f"/dedup/register/{rid2}")
    resp = client.get(f"/dedup/duplicates/{rid2}")
    assert resp.status_code == 200
    assert rid1 in resp.get_json()["duplicates"]


def test_all_duplicates(store, client):
    rid1 = _post_webhook(client, body=b"group1")
    rid2 = _post_webhook(client, body=b"group1")
    rid3 = _post_webhook(client, body=b"unique")
    for rid in [rid1, rid2, rid3]:
        client.post(f"/dedup/register/{rid}")
    resp = client.get("/dedup/all")
    assert resp.status_code == 200
    groups = resp.get_json()["duplicate_groups"]
    all_ids = [rid for ids in groups.values() for rid in ids]
    assert rid1 in all_ids
    assert rid2 in all_ids
    assert rid3 not in all_ids


def test_clear_dedup(store, client):
    rid = _post_webhook(client)
    client.post(f"/dedup/register/{rid}")
    resp = client.delete("/dedup/clear")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "cleared"
    # After clear, no duplicate groups
    resp2 = client.get("/dedup/all")
    assert resp2.get_json()["duplicate_groups"] == {}
