"""Tests for hookdrop/enrichment_routes.py"""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop import enrichment as enrich_module


@pytest.fixture
def store():
    s = RequestStore()
    enrich_module.reset_enrichments()
    return s


@pytest.fixture
def client(store):
    app = create_app(store)
    from hookdrop.enrichment_routes import init_enrichment_routes
    init_enrichment_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client, path="/hook", method="POST"):
    resp = client.open(path, method=method, json={"event": "test"})
    return resp.get_json()["id"]


def test_get_all_enrichments_empty(client):
    rid = _post_webhook(client)
    resp = client.get(f"/requests/{rid}/enrichments")
    assert resp.status_code == 200
    assert resp.get_json() == {}


def test_set_and_get_enrichment(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/enrichments/env", json={"value": "production"})
    assert resp.status_code == 200
    resp2 = client.get(f"/requests/{rid}/enrichments/env")
    assert resp2.status_code == 200
    assert resp2.get_json()["value"] == "production"


def test_set_enrichment_not_found(client):
    resp = client.put("/requests/bad-id/enrichments/env", json={"value": "x"})
    assert resp.status_code == 404


def test_set_enrichment_missing_value(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/enrichments/env", json={})
    assert resp.status_code == 400


def test_get_enrichment_key_not_found(client):
    rid = _post_webhook(client)
    resp = client.get(f"/requests/{rid}/enrichments/missing")
    assert resp.status_code == 404


def test_delete_enrichment(client):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/enrichments/tag", json={"value": "v1"})
    resp = client.delete(f"/requests/{rid}/enrichments/tag")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "tag"


def test_delete_enrichment_missing_key(client):
    rid = _post_webhook(client)
    resp = client.delete(f"/requests/{rid}/enrichments/ghost")
    assert resp.status_code == 404


def test_clear_all_enrichments(client):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/enrichments/a", json={"value": 1})
    client.put(f"/requests/{rid}/enrichments/b", json={"value": 2})
    resp = client.delete(f"/requests/{rid}/enrichments")
    assert resp.status_code == 200
    data = client.get(f"/requests/{rid}/enrichments").get_json()
    assert data == {}


def test_all_enrichments_endpoint(client):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/enrichments/env", json={"value": "qa"})
    resp = client.get("/enrichments")
    assert resp.status_code == 200
    assert rid in resp.get_json()
