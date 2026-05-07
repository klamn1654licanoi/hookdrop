"""Integration tests for pipeline Flask routes."""

import pytest
from hookdrop.receiver import create_app
from hookdrop.pipeline_routes import init_pipeline_routes
from hookdrop import pipeline as pl


@pytest.fixture
def app():
    from hookdrop.storage import RequestStore
    store = RequestStore()
    application = create_app(store)
    init_pipeline_routes(application)
    application.config["TESTING"] = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(autouse=True)
def reset():
    pl.clear_all()
    yield
    pl.clear_all()


def test_list_pipelines_empty(client):
    r = client.get("/pipelines")
    assert r.status_code == 200
    assert r.get_json() == []


def test_create_pipeline(client):
    r = client.post("/pipelines", json={"name": "test-pipe"})
    assert r.status_code == 201
    assert r.get_json()["name"] == "test-pipe"


def test_create_pipeline_missing_name(client):
    r = client.post("/pipelines", json={})
    assert r.status_code == 400


def test_create_pipeline_duplicate(client):
    client.post("/pipelines", json={"name": "dup"})
    r = client.post("/pipelines", json={"name": "dup"})
    assert r.status_code == 409


def test_get_pipeline(client):
    client.post("/pipelines", json={"name": "p1"})
    r = client.get("/pipelines/p1")
    assert r.status_code == 200
    assert r.get_json()["name"] == "p1"


def test_get_pipeline_not_found(client):
    r = client.get("/pipelines/ghost")
    assert r.status_code == 404


def test_delete_pipeline(client):
    client.post("/pipelines", json={"name": "del-me"})
    r = client.delete("/pipelines/del-me")
    assert r.status_code == 204
    assert client.get("/pipelines/del-me").status_code == 404


def test_add_step(client):
    client.post("/pipelines", json={"name": "pipe"})
    r = client.post("/pipelines/pipe/steps", json={"type": "tag", "config": {"value": "v1"}})
    assert r.status_code == 201
    assert r.get_json()["type"] == "tag"


def test_add_step_invalid_type(client):
    client.post("/pipelines", json={"name": "pipe"})
    r = client.post("/pipelines/pipe/steps", json={"type": "invalid", "config": {}})
    assert r.status_code == 400


def test_remove_step(client):
    client.post("/pipelines", json={"name": "pipe"})
    client.post("/pipelines/pipe/steps", json={"type": "tag", "config": {}})
    r = client.delete("/pipelines/pipe/steps/0")
    assert r.status_code == 204


def test_remove_step_out_of_range(client):
    client.post("/pipelines", json={"name": "pipe"})
    r = client.delete("/pipelines/pipe/steps/99")
    assert r.status_code == 404


def test_clear_steps(client):
    client.post("/pipelines", json={"name": "pipe"})
    client.post("/pipelines/pipe/steps", json={"type": "filter", "config": {}})
    r = client.delete("/pipelines/pipe/steps")
    assert r.status_code == 204
    p = client.get("/pipelines/pipe").get_json()
    assert p["steps"] == []
