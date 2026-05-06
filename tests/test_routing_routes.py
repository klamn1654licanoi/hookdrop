"""Integration tests for routing_routes.py via Flask test client."""

import pytest
from unittest.mock import patch, MagicMock
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop import routing


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    from hookdrop.routing_routes import init_routing_routes
    init_routing_routes(app, store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_rules():
    routing.clear_rules()
    yield
    routing.clear_rules()


def _post_webhook(client, path="/hook", body=b"data"):
    return client.post(path, data=body, headers={"X-Source": "test"})


def test_list_rules_empty(client):
    resp = client.get("/routing/rules")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_rule(client):
    resp = client.post("/routing/rules", json={"name": "r1", "target_url": "http://x.com"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "r1"
    assert data["enabled"] is True


def test_add_rule_missing_fields(client):
    resp = client.post("/routing/rules", json={"name": "r1"})
    assert resp.status_code == 400


def test_add_rule_duplicate(client):
    client.post("/routing/rules", json={"name": "r1", "target_url": "http://x.com"})
    resp = client.post("/routing/rules", json={"name": "r1", "target_url": "http://y.com"})
    assert resp.status_code == 409


def test_get_rule(client):
    client.post("/routing/rules", json={"name": "r1", "target_url": "http://x.com"})
    resp = client.get("/routing/rules/r1")
    assert resp.status_code == 200
    assert resp.get_json()["target_url"] == "http://x.com"


def test_get_rule_not_found(client):
    resp = client.get("/routing/rules/ghost")
    assert resp.status_code == 404


def test_delete_rule(client):
    client.post("/routing/rules", json={"name": "r1", "target_url": "http://x.com"})
    resp = client.delete("/routing/rules/r1")
    assert resp.status_code == 200
    assert routing.get_rule("r1") is None


def test_enable_disable_rule(client):
    client.post("/routing/rules", json={"name": "r1", "target_url": "http://x.com"})
    resp = client.post("/routing/rules/r1/disable")
    assert resp.status_code == 200
    assert resp.get_json()["enabled"] is False
    resp = client.post("/routing/rules/r1/enable")
    assert resp.get_json()["enabled"] is True


def test_dispatch_success(client):
    _post_webhook(client)
    req_id = client.get("/requests").get_json()[0]["id"]
    client.post("/routing/rules", json={"name": "fwd", "target_url": "http://target.com"})
    mock_resp = MagicMock(status_code=202)
    with patch("hookdrop.routing.http_requests.request", return_value=mock_resp):
        resp = client.post(f"/routing/dispatch/{req_id}")
    assert resp.status_code == 200
    assert resp.get_json()["dispatched"][0]["ok"] is True


def test_dispatch_not_found(client):
    client.post("/routing/rules", json={"name": "fwd", "target_url": "http://target.com"})
    resp = client.post("/routing/dispatch/nonexistent")
    assert resp.status_code == 404
