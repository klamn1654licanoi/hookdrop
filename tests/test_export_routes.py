"""Integration tests for export HTTP routes."""

import json
import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clear_store(store):
    store.clear()


def _post_webhook(client, body=None, path="/hook"):
    return client.post(
        path,
        data=body or '{"event": "test"}',
        content_type="application/json",
    )


def test_export_json_empty(client):
    resp = client.get("/export/json")
    assert resp.status_code == 200
    assert json.loads(resp.data) == []


def test_export_json_after_receive(client):
    _post_webhook(client)
    resp = client.get("/export/json")
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert len(data) == 1
    assert data[0]["method"] == "POST"


def test_export_curl_empty(client):
    resp = client.get("/export/curl")
    assert resp.status_code == 200
    assert resp.data == b""


def test_export_curl_after_receive(client):
    _post_webhook(client)
    resp = client.get("/export/curl")
    assert resp.status_code == 200
    assert b"curl" in resp.data


def test_export_curl_with_target(client):
    _post_webhook(client)
    resp = client.get("/export/curl?target=http://remote.example.com/hook")
    assert b"remote.example.com" in resp.data


def test_export_curl_single_not_found(client):
    resp = client.get("/export/curl/nonexistent-id")
    assert resp.status_code == 404


def test_export_curl_single_found(client, store):
    _post_webhook(client)
    req_id = store.all()[0].id
    resp = client.get(f"/export/curl/{req_id}")
    assert resp.status_code == 200
    assert b"curl" in resp.data
