import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.priority_routes import init_priority_routes
from hookdrop import priority as priority_module


@pytest.fixture
def store():
    s = RequestStore()
    priority_module.clear_priorities()
    return s


@pytest.fixture
def client(store):
    app = create_app(store)
    init_priority_routes(app, store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _post_webhook(client):
    resp = client.post("/webhook", json={"event": "test"}, headers={"x-source": "pytest"})
    assert resp.status_code == 200
    return resp.get_json()["id"]


def test_get_priority_unset(client):
    rid = _post_webhook(client)
    resp = client.get(f"/requests/{rid}/priority")
    assert resp.status_code == 200
    assert resp.get_json()["priority"] is None


def test_set_and_get_priority(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/priority", json={"priority": "high"})
    assert resp.status_code == 200
    assert resp.get_json()["priority"] == "high"
    resp2 = client.get(f"/requests/{rid}/priority")
    assert resp2.get_json()["priority"] == "high"


def test_set_priority_invalid_level(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/priority", json={"priority": "extreme"})
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_set_priority_missing_field(client):
    rid = _post_webhook(client)
    resp = client.put(f"/requests/{rid}/priority", json={})
    assert resp.status_code == 400


def test_set_priority_not_found(client):
    resp = client.put("/requests/fake-id/priority", json={"priority": "low"})
    assert resp.status_code == 404


def test_remove_priority(client):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/priority", json={"priority": "critical"})
    resp = client.delete(f"/requests/{rid}/priority")
    assert resp.status_code == 200
    assert resp.get_json()["removed"] is True


def test_remove_priority_not_set(client):
    rid = _post_webhook(client)
    resp = client.delete(f"/requests/{rid}/priority")
    assert resp.status_code == 404


def test_filter_by_priority_route(client):
    r1 = _post_webhook(client)
    r2 = _post_webhook(client)
    client.put(f"/requests/{r1}/priority", json={"priority": "low"})
    client.put(f"/requests/{r2}/priority", json={"priority": "high"})
    resp = client.get("/requests/priority/low")
    assert resp.status_code == 200
    ids = [r["id"] for r in resp.get_json()]
    assert r1 in ids
    assert r2 not in ids


def test_all_priorities_route(client):
    r1 = _post_webhook(client)
    client.put(f"/requests/{r1}/priority", json={"priority": "normal"})
    resp = client.get("/priorities")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data[r1] == "normal"
