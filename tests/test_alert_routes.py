import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.alert_routes import init_alert_routes
from hookdrop import alerts


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_alert_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_alerts():
    alerts.clear_alerts()
    yield
    alerts.clear_alerts()


def _post_webhook(client, method="POST", path="/hook"):
    return client.open(path, method=method, data=b"hello", content_type="application/json")


def test_list_alerts_empty(client):
    resp = client.get("/alerts")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_add_alert(client):
    resp = client.post("/alerts", json={"name": "on_post", "condition": "method", "value": "POST"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "on_post"


def test_add_alert_missing_fields(client):
    resp = client.post("/alerts", json={"name": "broken"})
    assert resp.status_code == 400


def test_get_alert(client):
    client.post("/alerts", json={"name": "r1", "condition": "method", "value": "GET"})
    resp = client.get("/alerts/r1")
    assert resp.status_code == 200
    assert resp.get_json()["condition"] == "method"


def test_get_alert_not_found(client):
    resp = client.get("/alerts/ghost")
    assert resp.status_code == 404


def test_delete_alert(client):
    client.post("/alerts", json={"name": "temp", "condition": "method", "value": "DELETE"})
    resp = client.delete("/alerts/temp")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "temp"


def test_delete_alert_not_found(client):
    resp = client.delete("/alerts/nope")
    assert resp.status_code == 404


def test_scan(client):
    client.post("/alerts", json={"name": "on_post", "condition": "method", "value": "POST"})
    _post_webhook(client, method="POST")
    _post_webhook(client, method="POST")
    resp = client.get("/alerts/scan")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "on_post" in data
    assert len(data["on_post"]) == 2


def test_evaluate_request(client):
    client.post("/alerts", json={"name": "on_post", "condition": "method", "value": "POST"})
    _post_webhook(client, method="POST", path="/hook")
    from hookdrop.storage import RequestStore
    req_id = alerts.scan_store(
        client.application.extensions.get("store") or
        [app for app in [client.application]][0].view_functions
    )
    # Use scan to get an id, then evaluate
    scan_resp = client.get("/alerts/scan")
    ids = scan_resp.get_json().get("on_post", [])
    if ids:
        resp = client.get(f"/alerts/evaluate/{ids[0]}")
        assert resp.status_code == 200
        assert resp.get_json()["triggered"][0]["name"] == "on_post"


def test_evaluate_not_found(client):
    resp = client.get("/alerts/evaluate/nonexistent-id")
    assert resp.status_code == 404
