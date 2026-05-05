"""Tests for hookdrop/ttl_routes.py"""

import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.ttl_routes import init_ttl_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_ttl_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client, path="/webhook"):
    return client.post(path, data="hello", content_type="text/plain")


def test_summary_empty(client):
    res = client.get("/ttl/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 0
    assert data["active"] == 0
    assert data["expired"] == 0


def test_summary_with_requests(client):
    _post_webhook(client)
    _post_webhook(client)
    res = client.get("/ttl/summary?ttl=3600")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total"] == 2
    assert data["active"] == 2
    assert data["expired"] == 0


def test_expire_no_old_requests(client):
    _post_webhook(client)
    res = client.delete("/ttl/expire?ttl=3600")
    assert res.status_code == 200
    data = res.get_json()
    assert data["removed"] == 0
    assert data["ids"] == []


def test_expire_removes_all_with_zero_ttl(client):
    _post_webhook(client)
    _post_webhook(client)
    res = client.delete("/ttl/expire?ttl=0")
    assert res.status_code == 200
    data = res.get_json()
    assert data["removed"] == 2


def test_check_not_found(client):
    res = client.get("/ttl/check/nonexistent")
    assert res.status_code == 404
    assert "error" in res.get_json()


def test_check_fresh_request(client):
    _post_webhook(client)
    list_res = client.get("/requests")
    req_id = list_res.get_json()[0]["id"]
    res = client.get(f"/ttl/check/{req_id}?ttl=3600")
    assert res.status_code == 200
    data = res.get_json()
    assert data["expired"] is False
    assert data["seconds_remaining"] > 0
    assert data["ttl_seconds"] == 3600


def test_check_expired_request_zero_ttl(client):
    _post_webhook(client)
    list_res = client.get("/requests")
    req_id = list_res.get_json()[0]["id"]
    res = client.get(f"/ttl/check/{req_id}?ttl=0")
    assert res.status_code == 200
    data = res.get_json()
    assert data["expired"] is True
    assert data["seconds_remaining"] <= 0
