"""Tests for webhook_groups module and group_routes."""

import pytest
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop import webhook_groups as wg


@pytest.fixture
def store():
    s = RequestStore()
    yield s
    s.clear()


@pytest.fixture(autouse=True)
def reset_groups():
    wg.clear_all_groups()
    yield
    wg.clear_all_groups()


@pytest.fixture
def client(store):
    app = create_app(store)
    from hookdrop.group_routes import init_group_routes
    init_group_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "ping"}, headers={"X-Source": "test"})
    return resp.get_json()["id"]


def _make_request(store):
    from hookdrop.storage import WebhookRequest
    import datetime
    req = WebhookRequest(
        method="POST", path="/hooks", headers={}, body="{}",
        timestamp=datetime.datetime.utcnow().isoformat()
    )
    store.save(req)
    return req.id


def test_create_group(store):
    result = wg.create_group("alpha")
    assert result["created"] is True
    assert result["name"] == "alpha"


def test_create_group_duplicate(store):
    wg.create_group("alpha")
    result = wg.create_group("alpha")
    assert result["created"] is False


def test_list_groups_empty():
    assert wg.list_groups() == []


def test_list_groups_after_create():
    wg.create_group("beta")
    groups = wg.list_groups()
    assert any(g["name"] == "beta" for g in groups)


def test_add_to_group_success(store):
    rid = _make_request(store)
    wg.create_group("g1")
    ok = wg.add_to_group(store, "g1", rid)
    assert ok is True


def test_add_to_group_missing_group(store):
    rid = _make_request(store)
    ok = wg.add_to_group(store, "nonexistent", rid)
    assert ok is False


def test_add_to_group_missing_request(store):
    wg.create_group("g2")
    ok = wg.add_to_group(store, "g2", "bad-id")
    assert ok is False


def test_get_group_returns_requests(store):
    rid = _make_request(store)
    wg.create_group("g3")
    wg.add_to_group(store, "g3", rid)
    reqs = wg.get_group(store, "g3")
    assert reqs is not None
    assert any(r["id"] == rid for r in reqs)


def test_get_group_not_found(store):
    result = wg.get_group(store, "missing")
    assert result is None


def test_remove_from_group(store):
    rid = _make_request(store)
    wg.create_group("g4")
    wg.add_to_group(store, "g4", rid)
    ok = wg.remove_from_group("g4", rid)
    assert ok is True
    reqs = wg.get_group(store, "g4")
    assert reqs == []


def test_delete_group(store):
    wg.create_group("g5")
    deleted = wg.delete_group("g5")
    assert deleted is True
    assert wg.get_group(store, "g5") is None


def test_route_create_and_list(client):
    resp = client.post("/groups/mygroup")
    assert resp.status_code == 201
    resp2 = client.get("/groups")
    data = resp2.get_json()
    assert any(g["name"] == "mygroup" for g in data)


def test_route_add_and_get(client):
    rid = _post_webhook(client)
    client.post("/groups/mygroup")
    resp = client.post(f"/groups/mygroup/add/{rid}")
    assert resp.status_code == 200
    resp2 = client.get("/groups/mygroup")
    body = resp2.get_json()
    assert any(r["id"] == rid for r in body["requests"])


def test_route_delete_group(client):
    client.post("/groups/tmp")
    resp = client.delete("/groups/tmp")
    assert resp.status_code == 200
    resp2 = client.get("/groups/tmp")
    assert resp2.status_code == 404
