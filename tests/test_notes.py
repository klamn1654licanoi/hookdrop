"""Tests for notes module and routes."""

import pytest
from flask import Flask

from hookdrop.storage import RequestStore
from hookdrop.receiver import init_receiver
from hookdrop.notes import add_note, get_note, remove_note, requests_with_notes
from hookdrop.notes_routes import init_notes_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = Flask(__name__)
    app.config["TESTING"] = True
    init_receiver(app, store)
    init_notes_routes(app, store)
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clear_store(store):
    store.clear()


def _make_request(store):
    from hookdrop.storage import WebhookRequest
    import uuid, datetime
    req = WebhookRequest(
        id=str(uuid.uuid4()),
        method="POST",
        path="/hook",
        headers={},
        body="{}",
        timestamp=datetime.datetime.utcnow().isoformat(),
        meta={},
    )
    store.save(req)
    return req


# --- Unit tests ---

def test_add_and_get_note(store):
    req = _make_request(store)
    assert add_note(store, req.id, "hello") is True
    assert get_note(store, req.id) == "hello"


def test_get_note_no_note(store):
    req = _make_request(store)
    assert get_note(store, req.id) is None


def test_get_note_not_found(store):
    assert get_note(store, "nonexistent") is None


def test_add_note_not_found(store):
    assert add_note(store, "nonexistent", "hi") is False


def test_remove_note(store):
    req = _make_request(store)
    add_note(store, req.id, "to remove")
    assert remove_note(store, req.id) is True
    assert get_note(store, req.id) is None


def test_remove_note_not_found(store):
    assert remove_note(store, "nonexistent") is False


def test_requests_with_notes(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    add_note(store, r1.id, "important")
    noted = requests_with_notes(store)
    ids = [r.id for r in noted]
    assert r1.id in ids
    assert r2.id not in ids


# --- Route tests ---

def test_put_and_get_note_route(client, store):
    req = _make_request(store)
    rv = client.put(f"/requests/{req.id}/note", json={"note": "test note"})
    assert rv.status_code == 200
    rv2 = client.get(f"/requests/{req.id}/note")
    assert rv2.status_code == 200
    assert rv2.get_json()["note"] == "test note"


def test_delete_note_route(client, store):
    req = _make_request(store)
    client.put(f"/requests/{req.id}/note", json={"note": "bye"})
    rv = client.delete(f"/requests/{req.id}/note")
    assert rv.status_code == 200
    assert rv.get_json()["note"] is None


def test_put_note_not_found(client):
    rv = client.put("/requests/missing/note", json={"note": "x"})
    assert rv.status_code == 404


def test_list_noted_route(client, store):
    r1 = _make_request(store)
    _make_request(store)
    client.put(f"/requests/{r1.id}/note", json={"note": "flagged"})
    rv = client.get("/requests/noted")
    assert rv.status_code == 200
    data = rv.get_json()
    assert len(data) == 1
    assert data[0]["id"] == r1.id
