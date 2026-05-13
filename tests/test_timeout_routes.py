"""Integration tests for timeout routes."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.timeout_routes import init_timeout_routes
from hookdrop import timeouts
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def clear_rules():
    timeouts.clear_timeout_rules()
    yield
    timeouts.clear_timeout_rules()


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_timeout_routes(app, store)
    return app.test_client()


def _post_webhook(store: RequestStore, path: str = "/hook", duration: float = 1.0) -> WebhookRequest:
    req = WebhookRequest(
        method="POST",
        path=path,
        headers={},
        body="",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    req.duration = duration
    store.save(req)
    return req


def test_list_rules_empty(client):
    rv = client.get("/timeouts/rules")
    assert rv.status_code == 200
    assert rv.get_json() == {}


def test_add_and_get_rule(client):
    rv = client.post("/timeouts/rules", json={"path_prefix": "/api", "max_seconds": 3.0})
    assert rv.status_code == 201
    rv2 = client.get("/timeouts/rules/%2Fapi")
    assert rv2.status_code == 200
    assert rv2.get_json()["max_seconds"] == 3.0


def test_add_rule_missing_fields(client):
    rv = client.post("/timeouts/rules", json={"path_prefix": "/api"})
    assert rv.status_code == 400


def test_add_rule_invalid_seconds(client):
    rv = client.post("/timeouts/rules", json={"path_prefix": "/api", "max_seconds": -5})
    assert rv.status_code == 400


def test_delete_rule(client):
    client.post("/timeouts/rules", json={"path_prefix": "/api", "max_seconds": 1.0})
    rv = client.delete("/timeouts/rules/%2Fapi")
    assert rv.status_code == 204


def test_delete_rule_not_found(client):
    rv = client.delete("/timeouts/rules/%2Fmissing")
    assert rv.status_code == 404


def test_evaluate_timed_out(client, store):
    req = _post_webhook(store, path="/api/x", duration=10.0)
    client.post("/timeouts/rules", json={"path_prefix": "/api", "max_seconds": 2.0})
    rv = client.post(f"/timeouts/evaluate/{req.id}")
    assert rv.status_code == 200
    assert rv.get_json()["timed_out"] is True


def test_evaluate_not_found(client):
    client.post("/timeouts/rules", json={"path_prefix": "/api", "max_seconds": 1.0})
    rv = client.post("/timeouts/evaluate/nonexistent")
    assert rv.status_code == 404


def test_check_before_evaluate(client, store):
    req = _post_webhook(store)
    rv = client.get(f"/timeouts/check/{req.id}")
    assert rv.status_code == 404


def test_flagged_returns_timed_out(client, store):
    req = _post_webhook(store, path="/api", duration=9.0)
    client.post("/timeouts/rules", json={"path_prefix": "/api", "max_seconds": 1.0})
    rv = client.get("/timeouts/flagged")
    assert rv.status_code == 200
    ids = [r["id"] for r in rv.get_json()]
    assert req.id in ids
