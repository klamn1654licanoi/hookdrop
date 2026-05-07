import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.correlation_routes import init_correlation_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_correlation_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client):
    resp = client.post("/webhook", json={"event": "test"})
    return resp.get_json()["id"]


def test_get_correlation_not_found(client):
    resp = client.get("/requests/nonexistent/correlation")
    assert resp.status_code == 404


def test_set_correlation_not_found(client):
    resp = client.put("/requests/nonexistent/correlation", json={"correlation_id": "abc"})
    assert resp.status_code == 404


def test_set_and_get_correlation(client):
    req_id = _post_webhook(client)
    resp = client.put(f"/requests/{req_id}/correlation", json={"correlation_id": "corr-123"})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["correlation_id"] == "corr-123"

    resp = client.get(f"/requests/{req_id}/correlation")
    assert resp.status_code == 200
    assert resp.get_json()["correlation_id"] == "corr-123"


def test_set_correlation_missing_body(client):
    req_id = _post_webhook(client)
    resp = client.put(f"/requests/{req_id}/correlation", json={})
    assert resp.status_code == 400


def test_remove_correlation(client):
    req_id = _post_webhook(client)
    client.put(f"/requests/{req_id}/correlation", json={"correlation_id": "corr-xyz"})
    resp = client.delete(f"/requests/{req_id}/correlation")
    assert resp.status_code == 200
    assert resp.get_json()["correlation_id"] is None

    resp = client.get(f"/requests/{req_id}/correlation")
    assert resp.get_json()["correlation_id"] is None


def test_correlated_requests(client):
    id1 = _post_webhook(client)
    id2 = _post_webhook(client)
    client.put(f"/requests/{id1}/correlation", json={"correlation_id": "group-1"})
    client.put(f"/requests/{id2}/correlation", json={"correlation_id": "group-1"})

    resp = client.get("/correlations/group-1/requests")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["count"] == 2
    assert id1 in data["requests"]
    assert id2 in data["requests"]


def test_list_all_correlations(client):
    id1 = _post_webhook(client)
    id2 = _post_webhook(client)
    client.put(f"/requests/{id1}/correlation", json={"correlation_id": "alpha"})
    client.put(f"/requests/{id2}/correlation", json={"correlation_id": "beta"})

    resp = client.get("/correlations")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "alpha" in data["correlations"]
    assert "beta" in data["correlations"]
