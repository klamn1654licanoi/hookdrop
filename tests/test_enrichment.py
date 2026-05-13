"""Tests for hookdrop/enrichment.py"""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import enrichment as enrich_module
from datetime import datetime


@pytest.fixture
def store():
    s = RequestStore()
    enrich_module.reset_enrichments()
    return s


def _make_request(store, path="/hook", method="POST"):
    req = WebhookRequest(
        method=method,
        path=path,
        headers={"content-type": "application/json"},
        body="{}",
        timestamp=datetime.utcnow().isoformat(),
    )
    store.save(req)
    return req


def test_set_and_get_enrichment(store):
    req = _make_request(store)
    result = enrich_module.set_enrichment(store, req.id, "env", "production")
    assert result is True
    assert enrich_module.get_enrichment(req.id, "env") == "production"


def test_set_enrichment_not_found(store):
    result = enrich_module.set_enrichment(store, "nonexistent", "key", "val")
    assert result is False


def test_get_enrichment_missing_key(store):
    req = _make_request(store)
    assert enrich_module.get_enrichment(req.id, "missing") is None


def test_get_all_enrichments(store):
    req = _make_request(store)
    enrich_module.set_enrichment(store, req.id, "env", "staging")
    enrich_module.set_enrichment(store, req.id, "version", "2")
    data = enrich_module.get_all_enrichments(req.id)
    assert data == {"env": "staging", "version": "2"}


def test_remove_enrichment_existing(store):
    req = _make_request(store)
    enrich_module.set_enrichment(store, req.id, "env", "prod")
    removed = enrich_module.remove_enrichment(req.id, "env")
    assert removed is True
    assert enrich_module.get_enrichment(req.id, "env") is None


def test_remove_enrichment_missing(store):
    req = _make_request(store)
    removed = enrich_module.remove_enrichment(req.id, "nope")
    assert removed is False


def test_clear_enrichments(store):
    req = _make_request(store)
    enrich_module.set_enrichment(store, req.id, "a", 1)
    enrich_module.set_enrichment(store, req.id, "b", 2)
    enrich_module.clear_enrichments(req.id)
    assert enrich_module.get_all_enrichments(req.id) == {}


def test_filter_by_enrichment(store):
    r1 = _make_request(store, path="/a")
    r2 = _make_request(store, path="/b")
    enrich_module.set_enrichment(store, r1.id, "env", "prod")
    enrich_module.set_enrichment(store, r2.id, "env", "dev")
    results = enrich_module.filter_by_enrichment(store, "env", "prod")
    assert len(results) == 1
    assert results[0].id == r1.id


def test_list_all_enrichments(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    enrich_module.set_enrichment(store, r1.id, "x", 1)
    enrich_module.set_enrichment(store, r2.id, "y", 2)
    all_data = enrich_module.list_all_enrichments()
    assert r1.id in all_data
    assert r2.id in all_data
