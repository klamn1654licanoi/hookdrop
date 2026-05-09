"""Integration tests for throttle Flask routes."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop.throttle_routes import init_throttle_routes
import hookdrop.throttle as thr


@pytest.fixture()
def store():
    return RequestStore()


@pytest.fixture()
def client(store):
    app = create_app(store)
    init_throttle_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_rules():
    thr.clear_throttle_rules()
    yield
    thr.clear_throttle_rules()


def _post_webhook(client, path="/hook"):
    return client.post(path, json={"event": "test"})


def test_list_rules_empty(client):
    resp = client.get("/throttle/rules")
    assert resp.status_code == 200
    assert resp.get_json() == {}


def test_add_and_list_rule(client):
    resp = client.post("/throttle/rules", json={"key": "/hook", "max_requests": 5, "window_seconds": 60})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["key"] == "/hook"

    resp2 = client.get("/throttle/rules")
    assert "/hook" in resp2.get_json()


def test_add_rule_missing_fields(client):
    resp = client.post("/throttle/rules", json={"key": "/hook"})
    assert resp.status_code == 400


def test_get_rule(client):
    client.post("/throttle/rules", json={"key": "/hook", "max_requests": 3, "window_seconds": 30})
    resp = client.get("/throttle/rules//hook")
    assert resp.status_code == 200
    assert resp.get_json()["max_requests"] == 3


def test_get_rule_not_found(client):
    resp = client.get("/throttle/rules//missing")
    assert resp.status_code == 404


def test_delete_rule(client):
    client.post("/throttle/rules", json={"key": "/hook", "max_requests": 3, "window_seconds": 30})
    resp = client.delete("/throttle/rules//hook")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "/hook"


def test_delete_rule_not_found(client):
    resp = client.delete("/throttle/rules//nope")
    assert resp.status_code == 404


def test_check_throttle_no_rule(client):
    resp = client.get("/throttle/check//hook")
    assert resp.status_code == 200
    assert resp.get_json()["throttled"] is False


def test_summary_empty(client):
    resp = client.get("/throttle/summary")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_clear_rules(client):
    client.post("/throttle/rules", json={"key": "/a", "max_requests": 1, "window_seconds": 10})
    resp = client.delete("/throttle/rules")
    assert resp.status_code == 200
    assert client.get("/throttle/rules").get_json() == {}
