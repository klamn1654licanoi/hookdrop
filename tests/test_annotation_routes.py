"""Integration tests for annotation Flask routes."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop.annotation_routes import init_annotation_routes
from hookdrop import annotations as ann_module


@pytest.fixture()
def store():
    return RequestStore()


@pytest.fixture(autouse=True)
def clear_annotations():
    ann_module.reset_annotations()
    yield
    ann_module.reset_annotations()


@pytest.fixture()
def client(store):
    app = create_app(store)
    init_annotation_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "test"}, headers={"X-Source": "ci"})
    return resp.get_json()["id"]


def test_get_all_annotations_empty(client):
    rid = _post_webhook(client)
    resp = client.get(f"/requests/{rid}/annotations")
    assert resp.status_code == 200
    assert resp.get_json() == {}


def test_set_and_get_annotation(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/annotations/env", json={"value": "prod"})
    assert resp.status_code == 200
    assert resp.get_json()["value"] == "prod"

    resp = client.get(f"/requests/{rid}/annotations/env")
    assert resp.status_code == 200
    assert resp.get_json()["value"] == "prod"


def test_set_annotation_missing_value(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/annotations/env", json={})
    assert resp.status_code == 400


def test_get_annotation_not_found_request(client):
    resp = client.get("/requests/bad-id/annotations/env")
    assert resp.status_code == 404


def test_get_annotation_missing_key(client):
    rid = _post_webhook(client)
    resp = client.get(f"/requests/{rid}/annotations/missing")
    assert resp.status_code == 404


def test_delete_annotation(client):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/annotations/x", json={"value": 1})
    resp = client.delete(f"/requests/{rid}/annotations/x")
    assert resp.status_code == 200
    assert resp.get_json()["removed"] == "x"


def test_delete_annotation_not_found(client):
    rid = _post_webhook(client)
    resp = client.delete(f"/requests/{rid}/annotations/ghost")
    assert resp.status_code == 404


def test_all_annotations_global(client):
    r1 = _post_webhook(client)
    r2 = _post_webhook(client)
    client.put(f"/requests/{r1}/annotations/env", json={"value": "prod"})
    client.put(f"/requests/{r2}/annotations/env", json={"value": "staging"})
    resp = client.get("/annotations")
    assert resp.status_code == 200
    data = resp.get_json()
    assert r1 in data
    assert r2 in data


def test_filter_by_annotation(client):
    r1 = _post_webhook(client)
    r2 = _post_webhook(client)
    client.put(f"/requests/{r1}/annotations/team", json={"value": "backend"})
    client.put(f"/requests/{r2}/annotations/team", json={"value": "frontend"})
    resp = client.get("/annotations/filter?key=team&value=backend")
    assert resp.status_code == 200
    ids = resp.get_json()["request_ids"]
    assert r1 in ids
    assert r2 not in ids


def test_filter_missing_params(client):
    resp = client.get("/annotations/filter?key=team")
    assert resp.status_code == 400
