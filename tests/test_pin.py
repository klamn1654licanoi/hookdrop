import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.pin import pin_request, unpin_request, is_pinned, list_pinned, clear_pins
from hookdrop.pin_routes import init_pin_routes


@pytest.fixture
def store():
    s = RequestStore()
    s.meta = {}
    return s


@pytest.fixture
def client(store):
    app = create_app(store)
    init_pin_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "test"}, headers={"X-Source": "pytest"})
    return resp.get_json()["id"]


def test_pin_request_success(store):
    from hookdrop.storage import WebhookRequest
    import datetime
    req = WebhookRequest(id="abc", method="POST", path="/hooks", headers={}, body="", timestamp=datetime.datetime.utcnow().isoformat())
    store.save(req)
    assert pin_request(store, "abc") is True
    assert is_pinned(store, "abc") is True


def test_pin_request_not_found(store):
    assert pin_request(store, "missing") is False


def test_unpin_request(store):
    from hookdrop.storage import WebhookRequest
    import datetime
    req = WebhookRequest(id="xyz", method="GET", path="/hooks", headers={}, body="", timestamp=datetime.datetime.utcnow().isoformat())
    store.save(req)
    pin_request(store, "xyz")
    assert is_pinned(store, "xyz") is True
    unpin_request(store, "xyz")
    assert is_pinned(store, "xyz") is False


def test_list_pinned(store):
    from hookdrop.storage import WebhookRequest
    import datetime
    for i in range(3):
        req = WebhookRequest(id=f"r{i}", method="POST", path="/hooks", headers={}, body="", timestamp=datetime.datetime.utcnow().isoformat())
        store.save(req)
    pin_request(store, "r0")
    pin_request(store, "r2")
    pinned = list_pinned(store)
    assert len(pinned) == 2
    ids = {r.id for r in pinned}
    assert ids == {"r0", "r2"}


def test_clear_pins(store):
    from hookdrop.storage import WebhookRequest
    import datetime
    for i in range(3):
        req = WebhookRequest(id=f"p{i}", method="POST", path="/hooks", headers={}, body="", timestamp=datetime.datetime.utcnow().isoformat())
        store.save(req)
        pin_request(store, f"p{i}")
    count = clear_pins(store)
    assert count == 3
    assert list_pinned(store) == []


def test_pin_route_post_and_get(client):
    rid = _post_webhook(client)
    resp = client.post(f"/pins/{rid}")
    assert resp.status_code == 200
    assert resp.get_json()["pinned"] is True
    resp = client.get(f"/pins/{rid}")
    assert resp.get_json()["pinned"] is True


def test_pin_route_not_found(client):
    resp = client.post("/pins/nonexistent")
    assert resp.status_code == 404


def test_unpin_route(client):
    rid = _post_webhook(client)
    client.post(f"/pins/{rid}")
    resp = client.delete(f"/pins/{rid}")
    assert resp.status_code == 200
    assert resp.get_json()["pinned"] is False


def test_list_pinned_route(client):
    rid = _post_webhook(client)
    client.post(f"/pins/{rid}")
    resp = client.get("/pins")
    data = resp.get_json()
    assert any(r["id"] == rid for r in data)


def test_clear_pins_route(client):
    rid = _post_webhook(client)
    client.post(f"/pins/{rid}")
    resp = client.delete("/pins")
    assert resp.get_json()["cleared"] >= 1
    resp = client.get("/pins")
    assert resp.get_json() == []
