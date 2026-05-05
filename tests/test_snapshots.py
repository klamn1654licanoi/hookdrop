"""Unit tests for hookdrop/snapshots.py"""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import snapshots
from hookdrop.snapshots import (
    save_snapshot, load_snapshot, list_snapshots,
    delete_snapshot, get_snapshot, clear_all_snapshots,
)


@pytest.fixture(autouse=True)
def reset():
    clear_all_snapshots()
    yield
    clear_all_snapshots()


@pytest.fixture
def store():
    s = RequestStore()
    s.clear()
    return s


def _make_request(store, method="POST", path="/hook", body="{}"):
    req = WebhookRequest(
        method=method, path=path,
        headers={"content-type": "application/json"},
        body=body,
    )
    store.save(req)
    return req


def test_save_and_list(store):
    _make_request(store)
    count = save_snapshot(store, "snap1")
    assert count == 1
    assert "snap1" in list_snapshots()


def test_save_empty_store(store):
    count = save_snapshot(store, "empty")
    assert count == 0
    assert "empty" in list_snapshots()


def test_load_snapshot_restores(store):
    _make_request(store, path="/original")
    save_snapshot(store, "before")
    store.clear()
    assert len(store.all()) == 0
    loaded = load_snapshot(store, "before")
    assert loaded == 1
    assert store.all()[0].path == "/original"


def test_load_snapshot_not_found(store):
    result = load_snapshot(store, "nonexistent")
    assert result is None


def test_load_clears_existing(store):
    _make_request(store, path="/old")
    save_snapshot(store, "snap")
    _make_request(store, path="/new1")
    _make_request(store, path="/new2")
    load_snapshot(store, "snap")
    all_reqs = store.all()
    assert len(all_reqs) == 1
    assert all_reqs[0].path == "/old"


def test_get_snapshot(store):
    _make_request(store, method="GET", path="/ping")
    save_snapshot(store, "mysnap")
    data = get_snapshot("mysnap")
    assert data is not None
    assert len(data) == 1
    assert data[0]["path"] == "/ping"


def test_get_snapshot_not_found():
    assert get_snapshot("ghost") is None


def test_delete_snapshot(store):
    save_snapshot(store, "todelete")
    assert delete_snapshot("todelete") is True
    assert "todelete" not in list_snapshots()


def test_delete_snapshot_not_found():
    assert delete_snapshot("missing") is False


def test_multiple_snapshots(store):
    _make_request(store, path="/a")
    save_snapshot(store, "s1")
    _make_request(store, path="/b")
    save_snapshot(store, "s2")
    names = list_snapshots()
    assert "s1" in names
    assert "s2" in names
    assert get_snapshot("s1")[0]["path"] == "/a"
