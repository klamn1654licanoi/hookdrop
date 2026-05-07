"""Tests for hookdrop.flagging and flagging_routes."""

import pytest
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop import flagging


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture(autouse=True)
def reset_flags():
    flagging.clear_flags()
    yield
    flagging.clear_flags()


@pytest.fixture
def client(store):
    app = create_app(store)
    from hookdrop.flagging_routes import init_flagging_routes
    init_flagging_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _make_request(store):
    req = store.save(
        method="POST",
        path="/hook",
        headers={"content-type": "application/json"},
        body=b'{"x": 1}',
        query_string="",
    )
    return req.id


def _post_webhook(client):
    r = client.post("/webhook", json={"k": "v"})
    return r.get_json()["id"]


# --- unit tests ---

def test_add_flag_success(store):
    rid = _make_request(store)
    assert flagging.add_flag(store, rid, "urgent") is True
    assert "urgent" in flagging.get_flags(rid)


def test_add_flag_not_found(store):
    assert flagging.add_flag(store, "missing-id", "urgent") is False


def test_add_flag_no_duplicates(store):
    rid = _make_request(store)
    flagging.add_flag(store, rid, "review")
    flagging.add_flag(store, rid, "review")
    assert flagging.get_flags(rid).count("review") == 1


def test_remove_flag(store):
    rid = _make_request(store)
    flagging.add_flag(store, rid, "bug")
    assert flagging.remove_flag(store, rid, "bug") is True
    assert flagging.get_flags(rid) == []


def test_remove_flag_not_set(store):
    rid = _make_request(store)
    assert flagging.remove_flag(store, rid, "ghost") is False


def test_has_flag(store):
    rid = _make_request(store)
    flagging.add_flag(store, rid, "critical")
    assert flagging.has_flag(rid, "critical") is True
    assert flagging.has_flag(rid, "other") is False


def test_filter_by_flag(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    flagging.add_flag(store, r1, "vip")
    results = flagging.filter_by_flag(store, "vip")
    ids = [r.id for r in results]
    assert r1 in ids
    assert r2 not in ids


def test_list_all_flags(store):
    rid = _make_request(store)
    flagging.add_flag(store, rid, "z-flag")
    flagging.add_flag(store, rid, "a-flag")
    all_f = flagging.list_all_flags()
    assert rid in all_f
    assert all_f[rid] == ["a-flag", "z-flag"]


# --- route tests ---

def test_list_flags_not_found(client):
    r = client.get("/requests/nope/flags")
    assert r.status_code == 404


def test_add_and_list_flag_route(client, store):
    rid = _post_webhook(client)
    r = client.put(f"/requests/{rid}/flags/urgent")
    assert r.status_code == 201
    data = r.get_json()
    assert "urgent" in data["flags"]


def test_remove_flag_route(client, store):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/flags/temp")
    r = client.delete(f"/requests/{rid}/flags/temp")
    assert r.status_code == 200
    assert r.get_json()["flags"] == []


def test_all_flags_route(client, store):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/flags/watch")
    r = client.get("/flags")
    assert r.status_code == 200
    data = r.get_json()
    assert rid in data


def test_by_flag_route(client, store):
    rid = _post_webhook(client)
    client.put(f"/requests/{rid}/flags/special")
    r = client.get("/flags/special/requests")
    assert r.status_code == 200
    ids = [req["id"] for req in r.get_json()]
    assert rid in ids
