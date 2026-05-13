"""Unit tests for hookdrop/annotations.py"""

import pytest
from hookdrop.storage import RequestStore
from hookdrop import annotations as ann_module


@pytest.fixture(autouse=True)
def reset():
    ann_module.reset_annotations()
    yield
    ann_module.reset_annotations()


@pytest.fixture()
def store():
    return RequestStore()


def _make_request(store: RequestStore, method="POST", path="/hook"):
    from hookdrop.storage import WebhookRequest
    import uuid, datetime
    req = WebhookRequest(
        id=str(uuid.uuid4()),
        method=method,
        path=path,
        headers={},
        body="",
        timestamp=datetime.datetime.utcnow().isoformat(),
        status_code=200,
    )
    store.save(req)
    return req


def test_set_and_get_annotation(store):
    req = _make_request(store)
    ann_module.set_annotation(store, req.id, "env", "production")
    assert ann_module.get_annotation(store, req.id, "env") == "production"


def test_set_annotation_not_found(store):
    with pytest.raises(KeyError):
        ann_module.set_annotation(store, "nonexistent", "key", "val")


def test_get_annotation_missing_key(store):
    req = _make_request(store)
    assert ann_module.get_annotation(store, req.id, "missing") is None


def test_get_all_annotations(store):
    req = _make_request(store)
    ann_module.set_annotation(store, req.id, "a", 1)
    ann_module.set_annotation(store, req.id, "b", "hello")
    data = ann_module.get_all_annotations(store, req.id)
    assert data == {"a": 1, "b": "hello"}


def test_get_all_annotations_empty(store):
    req = _make_request(store)
    assert ann_module.get_all_annotations(store, req.id) == {}


def test_remove_annotation_existing(store):
    req = _make_request(store)
    ann_module.set_annotation(store, req.id, "x", 42)
    removed = ann_module.remove_annotation(store, req.id, "x")
    assert removed is True
    assert ann_module.get_annotation(store, req.id, "x") is None


def test_remove_annotation_missing(store):
    req = _make_request(store)
    removed = ann_module.remove_annotation(store, req.id, "ghost")
    assert removed is False


def test_filter_by_annotation(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    ann_module.set_annotation(store, r1.id, "env", "prod")
    ann_module.set_annotation(store, r2.id, "env", "staging")
    result = ann_module.filter_by_annotation(store, "env", "prod")
    assert r1.id in result
    assert r2.id not in result


def test_list_all_annotations(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    ann_module.set_annotation(store, r1.id, "k", "v1")
    ann_module.set_annotation(store, r2.id, "k", "v2")
    all_ann = ann_module.list_all_annotations()
    assert r1.id in all_ann
    assert r2.id in all_ann


def test_clear_annotations(store):
    req = _make_request(store)
    ann_module.set_annotation(store, req.id, "foo", "bar")
    ann_module.clear_annotations(req.id)
    assert ann_module.get_all_annotations(store, req.id) == {}
