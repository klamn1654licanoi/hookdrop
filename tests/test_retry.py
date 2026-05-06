import pytest
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
import hookdrop.retry as retry_module


@pytest.fixture
def store():
    s = RequestStore()
    retry_module.clear_retry_state()
    return s


@pytest.fixture
def client(store):
    app = create_app(store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "test"}, headers={"X-Event": "ping"})
    return resp.get_json()["id"]


def test_set_and_get_policy(store):
    req_id = store.save("POST", "/hook", {}, "body")
    ok = retry_module.set_retry_policy(req_id, store, max_attempts=5, delay_seconds=2.0)
    assert ok is True
    policy = retry_module.get_retry_policy(req_id)
    assert policy["max_attempts"] == 5
    assert policy["delay_seconds"] == 2.0
    assert "created_at" in policy


def test_set_policy_not_found(store):
    ok = retry_module.set_retry_policy("nonexistent", store)
    assert ok is False


def test_remove_policy(store):
    req_id = store.save("GET", "/hook", {}, "")
    retry_module.set_retry_policy(req_id, store)
    removed = retry_module.remove_retry_policy(req_id)
    assert removed is True
    assert retry_module.get_retry_policy(req_id) is None


def test_remove_policy_not_found():
    assert retry_module.remove_retry_policy("ghost") is False


def test_record_and_get_history(store):
    req_id = store.save("POST", "/hook", {}, "data")
    retry_module.record_retry_attempt(req_id, success=False, status_code=500)
    retry_module.record_retry_attempt(req_id, success=True, status_code=200)
    history = retry_module.get_retry_history(req_id)
    assert len(history) == 2
    assert history[0]["success"] is False
    assert history[0]["status_code"] == 500
    assert history[1]["success"] is True


def test_retry_summary_exhausted(store):
    req_id = store.save("POST", "/hook", {}, "data")
    retry_module.set_retry_policy(req_id, store, max_attempts=2)
    retry_module.record_retry_attempt(req_id, success=False)
    retry_module.record_retry_attempt(req_id, success=False)
    summary = retry_module.retry_summary(req_id)
    assert summary["attempts"] == 2
    assert summary["failures"] == 2
    assert summary["exhausted"] is True


def test_retry_summary_no_policy(store):
    req_id = store.save("GET", "/hook", {}, "")
    summary = retry_module.retry_summary(req_id)
    assert summary["policy"] is None
    assert summary["exhausted"] is False


def test_route_set_policy(client):
    req_id = _post_webhook(client)
    resp = client.post(f"/requests/{req_id}/retry/policy", json={"max_attempts": 4, "delay_seconds": 1.5})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["max_attempts"] == 4


def test_route_get_policy_not_found(client):
    resp = client.get("/requests/missing/retry/policy")
    assert resp.status_code == 404


def test_route_delete_policy(client):
    req_id = _post_webhook(client)
    client.post(f"/requests/{req_id}/retry/policy", json={})
    resp = client.delete(f"/requests/{req_id}/retry/policy")
    assert resp.status_code == 204


def test_route_history_empty(client):
    req_id = _post_webhook(client)
    resp = client.get(f"/requests/{req_id}/retry/history")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_route_summary(client):
    req_id = _post_webhook(client)
    resp = client.get(f"/requests/{req_id}/retry/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["request_id"] == req_id
    assert data["attempts"] == 0
