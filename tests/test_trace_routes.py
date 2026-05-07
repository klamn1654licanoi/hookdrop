"""Integration tests for trace routes."""

import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.trace_routes import init_trace_routes
from hookdrop.trace import clear_traces


@pytest.fixture()
def store():
    return RequestStore()


@pytest.fixture()
def client(store):
    app = create_app(store)
    init_trace_routes(app, store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def reset_traces():
    clear_traces()
    yield
    clear_traces()


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "test"}, headers={"X-Source": "pytest"})
    return resp.get_json()["id"]


def test_list_traces_empty(client):
    resp = client.get("/traces")
    assert resp.status_code == 200
    assert resp.get_json() == {}


def test_create_trace(client):
    resp = client.post("/traces", json={"trace_id": "my-trace"})
    assert resp.status_code == 201
    assert resp.get_json()["trace_id"] == "my-trace"


def test_create_trace_auto_id(client):
    resp = client.post("/traces", json={})
    assert resp.status_code == 201
    assert "trace_id" in resp.get_json()


def test_get_trace_not_found(client):
    resp = client.get("/traces/ghost")
    assert resp.status_code == 404


def test_attach_and_get_trace(client):
    rid = _post_webhook(client)
    client.post("/traces", json={"trace_id": "t1"})
    resp = client.post(f"/traces/t1/attach/{rid}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["trace_id"] == "t1"
    assert data["request_id"] == rid

    resp2 = client.get("/traces/t1")
    assert resp2.status_code == 200
    assert rid in resp2.get_json()["requests"]


def test_attach_request_not_found(client):
    client.post("/traces", json={"trace_id": "t1"})
    resp = client.post("/traces/t1/attach/nonexistent")
    assert resp.status_code == 404


def test_detach_request(client):
    rid = _post_webhook(client)
    client.post("/traces", json={"trace_id": "t1"})
    client.post(f"/traces/t1/attach/{rid}")
    resp = client.delete(f"/traces/request/{rid}")
    assert resp.status_code == 200
    assert resp.get_json()["detached"] == rid


def test_detach_not_traced(client):
    resp = client.delete("/traces/request/nobody")
    assert resp.status_code == 404


def test_delete_trace(client):
    client.post("/traces", json={"trace_id": "t1"})
    resp = client.delete("/traces/t1")
    assert resp.status_code == 200
    assert resp.get_json()["deleted"] == "t1"

    resp2 = client.get("/traces/t1")
    assert resp2.status_code == 404


def test_get_trace_for_request(client):
    rid = _post_webhook(client)
    client.post("/traces", json={"trace_id": "t2"})
    client.post(f"/traces/t2/attach/{rid}")
    resp = client.get(f"/traces/request/{rid}")
    assert resp.status_code == 200
    assert resp.get_json()["trace_id"] == "t2"
