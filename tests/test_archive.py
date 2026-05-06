"""Tests for archive module and routes."""

import pytest
from hookdrop.storage import RequestStore
from hookdrop.receiver import create_app
from hookdrop.archive import (
    archive_request,
    unarchive_request,
    is_archived,
    list_archived,
    list_active,
    clear_archived,
)


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, method="POST", path="/hook"):
    from hookdrop.storage import WebhookRequest
    import uuid
    req = WebhookRequest(
        id=str(uuid.uuid4()),
        method=method,
        path=path,
        headers={},
        body="",
        timestamp=__import__("datetime").datetime.utcnow().isoformat(),
    )
    store.save(req)
    return req


@pytest.fixture
def client(store):
    app = create_app(store)
    app.config["TESTING"] = True
    from hookdrop.archive_routes import init_archive_routes
    init_archive_routes(app, store)
    with app.test_client() as c:
        yield c


def test_archive_request_success(store):
    req = _make_request(store)
    assert archive_request(store, req.id) is True
    assert is_archived(store, req.id) is True


def test_archive_request_not_found(store):
    assert archive_request(store, "nonexistent") is False


def test_unarchive_request(store):
    req = _make_request(store)
    archive_request(store, req.id)
    assert unarchive_request(store, req.id) is True
    assert is_archived(store, req.id) is False


def test_unarchive_not_found(store):
    assert unarchive_request(store, "missing") is False


def test_list_archived_and_active(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    archive_request(store, r1.id)
    archived = list_archived(store)
    active = list_active(store)
    assert any(r.id == r1.id for r in archived)
    assert any(r.id == r2.id for r in active)
    assert not any(r.id == r2.id for r in archived)


def test_clear_archived(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    archive_request(store, r1.id)
    archive_request(store, r2.id)
    count = clear_archived(store)
    assert count == 2
    assert list_archived(store) == []


def test_route_archive_and_status(client, store):
    req = _make_request(store)
    resp = client.post(f"/archive/{req.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["archived"] is True

    resp = client.get(f"/archive/{req.id}/status")
    assert resp.status_code == 200
    assert resp.get_json()["archived"] is True


def test_route_unarchive(client, store):
    req = _make_request(store)
    client.post(f"/archive/{req.id}")
    resp = client.delete(f"/archive/{req.id}")
    assert resp.status_code == 200
    assert resp.get_json()["archived"] is False


def test_route_archive_not_found(client):
    resp = client.post("/archive/ghost")
    assert resp.status_code == 404


def test_route_clear_archived(client, store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    client.post(f"/archive/{r1.id}")
    client.post(f"/archive/{r2.id}")
    resp = client.post("/archive/clear")
    assert resp.status_code == 200
    assert resp.get_json()["cleared"] == 2
