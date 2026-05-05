"""Integration tests for diff routes."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import init_receiver
from hookdrop.diff_routes import init_diff_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_receiver(app, store)
    init_diff_routes(app, store)
    return app.test_client()


def _post_webhook(client, path="/webhook", method="POST", body="{}", headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    resp = client.open(path, method=method, data=body, headers=h)
    return resp.get_json()["id"]


def test_diff_not_found_a(client):
    id_b = _post_webhook(client)
    resp = client.get(f"/diff/nonexistent/{id_b}")
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["error"]


def test_diff_not_found_b(client):
    id_a = _post_webhook(client)
    resp = client.get(f"/diff/{id_a}/nonexistent")
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["error"]


def test_diff_same_request(client):
    id_a = _post_webhook(client, body='{"x": 1}')
    resp = client.get(f"/diff/{id_a}/{id_a}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["method"]["changed"] is False
    assert data["path"]["changed"] is False
    assert data["body"]["changed"] is False


def test_diff_different_methods(client):
    id_a = _post_webhook(client, method="POST", path="/hook")
    id_b = _post_webhook(client, method="GET", path="/hook")
    resp = client.get(f"/diff/{id_a}/{id_b}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["method"]["changed"] is True
    assert data["method"]["from"] == "POST"
    assert data["method"]["to"] == "GET"


def test_diff_different_bodies(client):
    id_a = _post_webhook(client, body='{"a": 1}')
    id_b = _post_webhook(client, body='{"b": 2}')
    resp = client.get(f"/diff/{id_a}/{id_b}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["body"]["changed"] is True
