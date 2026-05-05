import pytest
from datetime import datetime, timedelta

from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.rate_routes import init_rate_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_rate_routes(app, store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _post_webhook(client, method="POST", path="/hook"):
    return client.open(path, method=method, data="payload", content_type="text/plain")


def test_summary_empty(client):
    resp = client.get("/rate/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 0
    assert data["window_seconds"] == 60


def test_summary_with_requests(client):
    _post_webhook(client, method="POST", path="/hook")
    _post_webhook(client, method="GET", path="/other")
    resp = client.get("/rate/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 2


def test_summary_custom_window(client):
    resp = client.get("/rate/summary?window=120")
    assert resp.status_code == 200
    assert resp.get_json()["window_seconds"] == 120


def test_summary_invalid_window(client):
    resp = client.get("/rate/summary?window=abc")
    assert resp.status_code == 400


def test_summary_negative_window(client):
    resp = client.get("/rate/summary?window=-10")
    assert resp.status_code == 400


def test_per_minute(client):
    _post_webhook(client)
    resp = client.get("/rate/per-minute")
    assert resp.status_code == 200
    assert "requests_per_minute" in resp.get_json()


def test_by_method(client):
    _post_webhook(client, method="POST")
    _post_webhook(client, method="GET")
    resp = client.get("/rate/by-method")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("POST", 0) >= 1


def test_by_path(client):
    _post_webhook(client, path="/alpha")
    _post_webhook(client, path="/beta")
    resp = client.get("/rate/by-path")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "/alpha" in data or "/beta" in data
