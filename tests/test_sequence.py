"""Tests for hookdrop.sequence and sequence_routes."""

import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop import sequence as seq_module
from hookdrop.sequence_routes import init_sequence_routes


@pytest.fixture()
def store():
    return RequestStore()


@pytest.fixture(autouse=True)
def reset_sequences():
    seq_module.clear_sequences()
    yield
    seq_module.clear_sequences()


@pytest.fixture()
def client(store):
    app = create_app(store)
    init_sequence_routes(app)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "ping"}, headers={"X-Test": "1"})
    return resp.get_json()["id"]


# --- unit tests for sequence module ---

def test_define_and_get_sequence(store):
    seq_module.define_sequence("s1", ["a", "b", "c"])
    result = seq_module.get_sequence("s1")
    assert result == {"name": "s1", "request_ids": ["a", "b", "c"]}


def test_define_sequence_empty_name_raises():
    with pytest.raises(ValueError):
        seq_module.define_sequence("", ["a"])


def test_define_sequence_empty_ids_raises():
    with pytest.raises(ValueError):
        seq_module.define_sequence("s1", [])


def test_delete_sequence_existing(store):
    seq_module.define_sequence("s1", ["a"])
    assert seq_module.delete_sequence("s1") is True
    assert seq_module.get_sequence("s1") is None


def test_delete_sequence_missing():
    assert seq_module.delete_sequence("nope") is False


def test_list_sequences():
    seq_module.define_sequence("s1", ["a"])
    seq_module.define_sequence("s2", ["b", "c"])
    names = {s["name"] for s in seq_module.list_sequences()}
    assert names == {"s1", "s2"}


def test_validate_sequence_all_found(store):
    rid = store.save("POST", "/hook", {}, "body")
    seq_module.define_sequence("full", [rid])
    report = seq_module.validate_sequence("full", store)
    assert report["valid"] is True
    assert rid in report["found"]
    assert report["missing"] == []


def test_validate_sequence_some_missing(store):
    rid = store.save("POST", "/hook", {}, "body")
    seq_module.define_sequence("partial", [rid, "ghost-id"])
    report = seq_module.validate_sequence("partial", store)
    assert report["valid"] is False
    assert "ghost-id" in report["missing"]


def test_validate_sequence_not_found_raises(store):
    with pytest.raises(KeyError):
        seq_module.validate_sequence("missing", store)


# --- route tests ---

def test_list_sequences_empty(client):
    resp = client.get("/sequences/")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_create_and_get_sequence(client):
    resp = client.post("/sequences/", json={"name": "flow1", "request_ids": ["x", "y"]})
    assert resp.status_code == 201
    resp2 = client.get("/sequences/flow1")
    assert resp2.status_code == 200
    assert resp2.get_json()["request_ids"] == ["x", "y"]


def test_create_sequence_missing_name(client):
    resp = client.post("/sequences/", json={"request_ids": ["a"]})
    assert resp.status_code == 400


def test_delete_sequence_route(client):
    client.post("/sequences/", json={"name": "del_me", "request_ids": ["z"]})
    resp = client.delete("/sequences/del_me")
    assert resp.status_code == 200
    assert client.get("/sequences/del_me").status_code == 404


def test_validate_sequence_route(client):
    rid = _post_webhook(client)
    client.post("/sequences/", json={"name": "v1", "request_ids": [rid]})
    resp = client.get("/sequences/v1/validate")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["valid"] is True
