import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import priority as priority_module
from datetime import datetime, timezone


@pytest.fixture
def store():
    s = RequestStore()
    priority_module.clear_priorities()
    return s


def _make_request(store, method="POST", path="/hook"):
    req = WebhookRequest(
        id=None,
        method=method,
        path=path,
        headers={"content-type": "application/json"},
        body="{}",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    store.save(req)
    return req


def test_set_and_get_priority(store):
    req = _make_request(store)
    result = priority_module.set_priority(store, req.id, "high")
    assert result is True
    assert priority_module.get_priority(req.id) == "high"


def test_set_priority_not_found(store):
    result = priority_module.set_priority(store, "nonexistent-id", "low")
    assert result is False


def test_set_invalid_priority(store):
    req = _make_request(store)
    with pytest.raises(ValueError, match="Invalid priority level"):
        priority_module.set_priority(store, req.id, "urgent")


def test_get_priority_unset(store):
    req = _make_request(store)
    assert priority_module.get_priority(req.id) is None


def test_remove_priority(store):
    req = _make_request(store)
    priority_module.set_priority(store, req.id, "critical")
    removed = priority_module.remove_priority(req.id)
    assert removed is True
    assert priority_module.get_priority(req.id) is None


def test_remove_priority_not_set(store):
    req = _make_request(store)
    assert priority_module.remove_priority(req.id) is False


def test_filter_by_priority(store):
    r1 = _make_request(store, path="/a")
    r2 = _make_request(store, path="/b")
    r3 = _make_request(store, path="/c")
    priority_module.set_priority(store, r1.id, "high")
    priority_module.set_priority(store, r2.id, "low")
    priority_module.set_priority(store, r3.id, "high")
    result = priority_module.filter_by_priority(store, "high")
    ids = {r.id for r in result}
    assert r1.id in ids
    assert r3.id in ids
    assert r2.id not in ids


def test_filter_by_invalid_priority(store):
    with pytest.raises(ValueError):
        priority_module.filter_by_priority(store, "mega")


def test_list_all_priorities(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    priority_module.set_priority(store, r1.id, "normal")
    priority_module.set_priority(store, r2.id, "critical")
    mapping = priority_module.list_all_priorities(store)
    assert mapping[r1.id] == "normal"
    assert mapping[r2.id] == "critical"
