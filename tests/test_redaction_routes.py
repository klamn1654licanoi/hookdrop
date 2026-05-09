"""Integration tests for redaction routes."""

import pytest

from hookdrop import redaction
from hookdrop.receiver import create_app
from hookdrop.redaction_routes import init_redaction_routes
from hookdrop.storage import RequestStore


@pytest.fixture()
def store():
    return RequestStore()


@pytest.fixture()
def client(store):
    app = create_app(store)
    init_redaction_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_rules():
    redaction.clear_rules()
    yield
    redaction.clear_rules()


def _post_webhook(client, headers=None, body=""):
    h = {"Content-Type": "application/json", **(headers or {})}
    return client.post("/hooks", data=body, headers=h)


def test_list_rules_empty(client):
    r = client.get("/redaction/rules")
    assert r.status_code == 200
    assert r.get_json() == {}


def test_add_rule(client):
    r = client.post("/redaction/rules", json={"field": "Authorization"})
    assert r.status_code == 201
    data = r.get_json()
    assert data["field"] == "Authorization"


def test_add_rule_missing_field(client):
    r = client.post("/redaction/rules", json={})
    assert r.status_code == 400


def test_remove_rule(client):
    client.post("/redaction/rules", json={"field": "X-Secret"})
    r = client.delete("/redaction/rules/X-Secret")
    assert r.status_code == 200
    assert r.get_json()["removed"] == "X-Secret"


def test_remove_rule_not_found(client):
    r = client.delete("/redaction/rules/nonexistent")
    assert r.status_code == 404


def test_clear_rules(client):
    client.post("/redaction/rules", json={"field": "Authorization"})
    r = client.delete("/redaction/rules")
    assert r.status_code == 200
    assert client.get("/redaction/rules").get_json() == {}


def test_preview_not_found(client):
    r = client.get("/redaction/preview/does-not-exist")
    assert r.status_code == 404


def test_preview_redacts_header(client, store):
    _post_webhook(client, headers={"Authorization": "Bearer secret"})
    req_id = store.all()[0].id
    client.post("/redaction/rules", json={"field": "Authorization"})
    r = client.get(f"/redaction/preview/{req_id}")
    assert r.status_code == 200
    data = r.get_json()
    assert data["headers"].get("Authorization") == "[REDACTED]"
