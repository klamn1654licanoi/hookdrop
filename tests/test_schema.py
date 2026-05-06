"""Tests for schema validation module and routes."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop import schema as schema_module


@pytest.fixture(autouse=True)
def reset_schemas():
    schema_module.clear_schemas()
    yield
    schema_module.clear_schemas()


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client, path="/hook", body='{"event": "ping"}'):
    return client.post(path, data=body, content_type="application/json")


# --- Unit tests for schema.py ---

def test_validate_body_valid():
    s = {"required": ["event"], "properties": {"event": {"type": "string"}}}
    valid, errors = schema_module.validate_body('{"event": "ping"}', s)
    assert valid is True
    assert errors == []


def test_validate_body_missing_required():
    s = {"required": ["event", "id"]}
    valid, errors = schema_module.validate_body('{"event": "ping"}', s)
    assert valid is False
    assert any("id" in e for e in errors)


def test_validate_body_wrong_type():
    s = {"properties": {"count": {"type": "integer"}}}
    valid, errors = schema_module.validate_body('{"count": "not-a-number"}', s)
    assert valid is False
    assert any("count" in e for e in errors)


def test_validate_body_invalid_json():
    s = {}
    valid, errors = schema_module.validate_body("not json", s)
    assert valid is False
    assert "not valid JSON" in errors[0]


def test_validate_request_no_schema():
    valid, errors = schema_module.validate_request("/any/path", '{"x": 1}')
    assert valid is True
    assert errors == []


def test_validate_request_matches_pattern():
    schema_module.register_schema(r"/hook", {"required": ["event"]})
    valid, errors = schema_module.validate_request("/hook", '{"other": 1}')
    assert valid is False


def test_list_and_unregister():
    schema_module.register_schema(r"/a", {"required": ["x"]})
    schema_module.register_schema(r"/b", {"required": ["y"]})
    all_s = schema_module.list_schemas()
    assert r"/a" in all_s and r"/b" in all_s
    removed = schema_module.unregister_schema(r"/a")
    assert removed is True
    assert r"/a" not in schema_module.list_schemas()


def test_unregister_nonexistent():
    assert schema_module.unregister_schema("/nope") is False


# --- Route tests ---

def test_list_schemas_empty(client):
    r = client.get("/schemas")
    assert r.status_code == 200
    assert r.get_json() == {}


def test_register_and_get_schema(client):
    payload = {"schema": {"required": ["event"]}}
    r = client.put("/schemas//hook", json=payload)
    assert r.status_code == 201
    r2 = client.get("/schemas//hook")
    assert r2.status_code == 200
    assert r2.get_json()["schema"]["required"] == ["event"]


def test_delete_schema(client):
    client.put("/schemas//hook", json={"schema": {}})
    r = client.delete("/schemas//hook")
    assert r.status_code == 200
    assert client.get("/schemas//hook").status_code == 404


def test_validate_route_not_found(client):
    r = client.get("/schemas/validate/nonexistent")
    assert r.status_code == 404


def test_validate_route_valid(client, store):
    _post_webhook(client, path="/hook", body='{"event": "ping"}')
    req_id = store.all()[0].id
    schema_module.register_schema(r"/hook", {"required": ["event"]})
    r = client.get(f"/schemas/validate/{req_id}")
    data = r.get_json()
    assert data["valid"] is True
    assert data["errors"] == []


def test_validate_route_invalid(client, store):
    _post_webhook(client, path="/hook", body='{"other": 1}')
    req_id = store.all()[0].id
    schema_module.register_schema(r"/hook", {"required": ["event"]})
    r = client.get(f"/schemas/validate/{req_id}")
    data = r.get_json()
    assert data["valid"] is False
    assert len(data["errors"]) > 0
