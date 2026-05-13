"""Integration tests for watchdog Flask routes."""

import pytest
from flask import Flask
from hookdrop import watchdog as wd
from hookdrop.watchdog_routes import init_watchdog_routes


@pytest.fixture
def app():
    a = Flask(__name__)
    a.config["TESTING"] = True
    init_watchdog_routes(a)
    return a


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_rules():
    wd.clear_watchdog_rules()
    yield
    wd.clear_watchdog_rules()


def test_list_rules_empty(client):
    resp = client.get("/watchdog/rules")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_rule_success(client):
    resp = client.post("/watchdog/rules", json={"name": "spike", "max_per_minute": 20})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "spike"
    assert data["max_per_minute"] == 20


def test_add_rule_missing_name(client):
    resp = client.post("/watchdog/rules", json={"max_per_minute": 10})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_add_rule_invalid_limits(client):
    resp = client.post("/watchdog/rules", json={"name": "bad", "min_per_minute": 100, "max_per_minute": 5})
    assert resp.status_code == 400


def test_get_rule_found(client):
    client.post("/watchdog/rules", json={"name": "found"})
    resp = client.get("/watchdog/rules/found")
    assert resp.status_code == 200
    assert resp.get_json()["name"] == "found"


def test_get_rule_not_found(client):
    resp = client.get("/watchdog/rules/missing")
    assert resp.status_code == 404


def test_delete_rule(client):
    client.post("/watchdog/rules", json={"name": "todelete"})
    resp = client.delete("/watchdog/rules/todelete")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "todelete"


def test_delete_rule_not_found(client):
    resp = client.delete("/watchdog/rules/ghost")
    assert resp.status_code == 404


def test_evaluate_all_empty(client):
    resp = client.get("/watchdog/evaluate")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_evaluate_one_not_found(client):
    resp = client.get("/watchdog/evaluate/nope")
    assert resp.status_code == 404


def test_evaluate_one_no_breach(client):
    client.post("/watchdog/rules", json={"name": "calm", "max_per_minute": 100})
    resp = client.get("/watchdog/evaluate/calm")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["breached"] is False


def test_clear_rules(client):
    client.post("/watchdog/rules", json={"name": "r1"})
    client.post("/watchdog/rules", json={"name": "r2"})
    resp = client.delete("/watchdog/rules")
    assert resp.status_code == 200
    assert resp.get_json()["cleared"] is True
    assert client.get("/watchdog/rules").get_json() == []
