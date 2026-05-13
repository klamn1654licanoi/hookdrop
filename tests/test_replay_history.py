"""Tests for replay history tracking."""

import pytest
from flask import Flask
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop import replay_history as rh
from hookdrop.replay_history_routes import init_replay_history_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_replay_history_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture(autouse=True)
def reset():
    rh.reset_all()
    yield
    rh.reset_all()


def _post_webhook(client):
    resp = client.post("/hooks", json={"event": "test"}, headers={"X-Event": "ping"})
    return resp.get_json()["id"]


def test_record_replay_success():
    attempt = rh.record_replay("abc", "http://example.com", 200)
    assert attempt["success"] is True
    assert attempt["status_code"] == 200
    assert attempt["error"] is None


def test_record_replay_failure_by_status():
    attempt = rh.record_replay("abc", "http://example.com", 500)
    assert attempt["success"] is False


def test_record_replay_failure_by_error():
    attempt = rh.record_replay("abc", "http://example.com", None, error="timeout")
    assert attempt["success"] is False
    assert attempt["error"] == "timeout"


def test_get_replay_history_empty():
    assert rh.get_replay_history("nonexistent") == []


def test_get_replay_history_multiple():
    rh.record_replay("r1", "http://a.com", 200)
    rh.record_replay("r1", "http://a.com", 404)
    history = rh.get_replay_history("r1")
    assert len(history) == 2
    assert history[0]["status_code"] == 200
    assert history[1]["status_code"] == 404


def test_replay_summary_empty():
    summary = rh.replay_summary("missing")
    assert summary["total"] == 0
    assert summary["last"] is None


def test_replay_summary_with_data():
    rh.record_replay("r2", "http://b.com", 200)
    rh.record_replay("r2", "http://b.com", 500)
    summary = rh.replay_summary("r2")
    assert summary["total"] == 2
    assert summary["successes"] == 1
    assert summary["failures"] == 1


def test_clear_replay_history():
    rh.record_replay("r3", "http://c.com", 200)
    result = rh.clear_replay_history("r3")
    assert result is True
    assert rh.get_replay_history("r3") == []


def test_clear_replay_history_not_found():
    assert rh.clear_replay_history("ghost") is False


def test_route_history_not_found(client):
    resp = client.get("/replay-history/nonexistent")
    assert resp.status_code == 404


def test_route_history_empty(client, store):
    rid = _post_webhook(client)
    resp = client.get(f"/replay-history/{rid}")
    assert resp.status_code == 200
    assert resp.get_json() == []


def test_route_summary(client, store):
    rid = _post_webhook(client)
    rh.record_replay(rid, "http://example.com", 200)
    resp = client.get(f"/replay-history/{rid}/summary")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total"] == 1
    assert data["successes"] == 1


def test_route_clear_history(client, store):
    rid = _post_webhook(client)
    rh.record_replay(rid, "http://example.com", 200)
    resp = client.delete(f"/replay-history/{rid}")
    assert resp.status_code == 200
    assert rh.get_replay_history(rid) == []
