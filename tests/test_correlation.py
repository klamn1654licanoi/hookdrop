"""Tests for hookdrop.correlation module."""

import pytest
from hookdrop.storage import RequestStore
from hookdrop import correlation as corr


@pytest.fixture
def store():
    s = RequestStore()
    corr.clear_correlations()
    yield s
    corr.clear_correlations()


def _make_request(store, method="POST", path="/hook"):
    from hookdrop.storage import WebhookRequest
    import time
    req = WebhookRequest(
        id=None,
        method=method,
        path=path,
        headers={},
        body="",
        timestamp=time.time(),
    )
    store.save(req)
    return req


def test_set_and_get_correlation(store):
    req = _make_request(store)
    result = corr.set_correlation(store, req.id, "corr-abc")
    assert result is True
    assert corr.get_correlation(req.id) == "corr-abc"


def test_set_correlation_not_found(store):
    result = corr.set_correlation(store, "nonexistent-id", "corr-xyz")
    assert result is False


def test_get_correlation_unset(store):
    req = _make_request(store)
    assert corr.get_correlation(req.id) is None


def test_remove_correlation(store):
    req = _make_request(store)
    corr.set_correlation(store, req.id, "corr-123")
    assert corr.remove_correlation(req.id) is True
    assert corr.get_correlation(req.id) is None


def test_remove_correlation_not_found(store):
    assert corr.remove_correlation("ghost-id") is False


def test_get_correlated_requests(store):
    req1 = _make_request(store, path="/a")
    req2 = _make_request(store, path="/b")
    req3 = _make_request(store, path="/c")
    corr.set_correlation(store, req1.id, "flow-1")
    corr.set_correlation(store, req2.id, "flow-1")
    corr.set_correlation(store, req3.id, "flow-2")
    results = corr.get_correlated_requests(store, "flow-1")
    ids = {r.id for r in results}
    assert req1.id in ids
    assert req2.id in ids
    assert req3.id not in ids


def test_get_correlated_requests_empty(store):
    results = corr.get_correlated_requests(store, "no-such-flow")
    assert results == []


def test_list_all_correlations(store):
    req1 = _make_request(store)
    req2 = _make_request(store)
    corr.set_correlation(store, req1.id, "flow-A")
    corr.set_correlation(store, req2.id, "flow-B")
    all_corr = corr.list_all_correlations()
    assert "flow-A" in all_corr
    assert "flow-B" in all_corr
    assert req1.id in all_corr["flow-A"]
    assert req2.id in all_corr["flow-B"]


def test_remove_correlation_cleans_empty_group(store):
    req = _make_request(store)
    corr.set_correlation(store, req.id, "solo-flow")
    corr.remove_correlation(req.id)
    all_corr = corr.list_all_correlations()
    assert "solo-flow" not in all_corr


def test_no_duplicate_in_group(store):
    req = _make_request(store)
    corr.set_correlation(store, req.id, "dup-flow")
    corr.set_correlation(store, req.id, "dup-flow")
    all_corr = corr.list_all_correlations()
    assert all_corr["dup-flow"].count(req.id) == 1
