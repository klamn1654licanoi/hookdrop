"""Unit tests for hookdrop/tags.py"""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.tags import add_tag, remove_tag, get_tags, filter_by_tag, list_all_tags


@pytest.fixture
def store():
    return RequestStore()


def _make_request(req_id="abc123", method="POST", path="/hook"):
    return WebhookRequest(
        id=req_id,
        method=method,
        path=path,
        headers={},
        body="",
        timestamp="2024-01-01T00:00:00",
        meta={},
    )


def test_add_tag_success(store):
    req = _make_request()
    store.save(req)
    result = add_tag(store, req.id, "important")
    assert result is True
    assert "important" in get_tags(store, req.id)


def test_add_tag_not_found(store):
    result = add_tag(store, "nonexistent", "tag")
    assert result is False


def test_add_tag_no_duplicates(store):
    req = _make_request()
    store.save(req)
    add_tag(store, req.id, "dup")
    add_tag(store, req.id, "dup")
    assert get_tags(store, req.id).count("dup") == 1


def test_remove_tag_success(store):
    req = _make_request()
    store.save(req)
    add_tag(store, req.id, "remove-me")
    result = remove_tag(store, req.id, "remove-me")
    assert result is True
    assert "remove-me" not in get_tags(store, req.id)


def test_remove_tag_not_found(store):
    result = remove_tag(store, "nonexistent", "tag")
    assert result is False


def test_remove_nonexistent_tag_is_safe(store):
    req = _make_request()
    store.save(req)
    result = remove_tag(store, req.id, "ghost")
    assert result is True
    assert get_tags(store, req.id) == []


def test_get_tags_not_found(store):
    assert get_tags(store, "missing") is None


def test_filter_by_tag(store):
    r1 = _make_request(req_id="r1")
    r2 = _make_request(req_id="r2")
    store.save(r1)
    store.save(r2)
    add_tag(store, "r1", "alpha")
    add_tag(store, "r2", "beta")
    results = filter_by_tag(store, "alpha")
    assert len(results) == 1
    assert results[0].id == "r1"


def test_list_all_tags(store):
    r1 = _make_request(req_id="r1")
    r2 = _make_request(req_id="r2")
    store.save(r1)
    store.save(r2)
    add_tag(store, "r1", "z-tag")
    add_tag(store, "r1", "a-tag")
    add_tag(store, "r2", "a-tag")
    tags = list_all_tags(store)
    assert tags == ["a-tag", "z-tag"]


def test_list_all_tags_empty(store):
    assert list_all_tags(store) == []
