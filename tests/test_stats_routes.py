import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.stats_routes import init_stats_routes
from hookdrop.receiver import create_app


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_stats_routes(app, store)
    return app.test_client(), store


def _post_webhook(flask_client, store, method="POST", path="/hook", body="{}"):
    from hookdrop.storage import WebhookRequest
    req = WebhookRequest(
        method=method,
        path=path,
        headers={"Content-Type": "application/json"},
        body=body,
        status_code=200,
    )
    store.save(req)


def test_stats_empty(client):
    c, store = client
    resp = c.get("/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["by_method"] == {}


def test_stats_after_requests(client):
    c, store = client
    _post_webhook(c, store, method="POST", path="/hook")
    _post_webhook(c, store, method="GET", path="/ping")
    _post_webhook(c, store, method="POST", path="/hook")
    resp = c.get("/stats")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 3
    assert data["by_method"]["POST"] == 2
    assert data["by_method"]["GET"] == 1
    assert data["by_path"]["/hook"] == 2


def test_top_method_empty(client):
    c, store = client
    resp = c.get("/stats/top-method")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["method"] is None


def test_top_method(client):
    c, store = client
    _post_webhook(c, store, method="DELETE", path="/x")
    _post_webhook(c, store, method="DELETE", path="/y")
    _post_webhook(c, store, method="POST", path="/z")
    resp = c.get("/stats/top-method")
    assert resp.status_code == 200
    assert resp.get_json()["method"] == "DELETE"


def test_top_path_empty(client):
    c, store = client
    resp = c.get("/stats/top-path")
    assert resp.status_code == 200
    assert resp.get_json()["path"] is None


def test_top_path(client):
    c, store = client
    _post_webhook(c, store, path="/events")
    _post_webhook(c, store, path="/events")
    _post_webhook(c, store, path="/other")
    resp = c.get("/stats/top-path")
    assert resp.status_code == 200
    assert resp.get_json()["path"] == "/events"
