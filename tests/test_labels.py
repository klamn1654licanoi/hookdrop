import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import labels as label_lib
from datetime import datetime


@pytest.fixture
def store():
    s = RequestStore()
    s._store = {}
    s._order = []
    return s


def _make_request(store, method='POST', path='/hook', body='hello'):
    req = WebhookRequest(
        method=method,
        path=path,
        headers={'content-type': 'application/json'},
        body=body,
        timestamp=datetime.utcnow().isoformat()
    )
    req.meta = {}
    store.save(req)
    return req


def test_set_and_get_label(store):
    req = _make_request(store)
    result = label_lib.set_label(store, req.id, 'urgent')
    assert result is True
    assert label_lib.get_label(store, req.id) == 'urgent'


def test_set_label_not_found(store):
    result = label_lib.set_label(store, 'nonexistent', 'urgent')
    assert result is False


def test_get_label_none_when_unset(store):
    req = _make_request(store)
    assert label_lib.get_label(store, req.id) is None


def test_get_label_not_found(store):
    assert label_lib.get_label(store, 'missing') is None


def test_label_normalized_lowercase(store):
    req = _make_request(store)
    label_lib.set_label(store, req.id, '  CRITICAL  ')
    assert label_lib.get_label(store, req.id) == 'critical'


def test_remove_label(store):
    req = _make_request(store)
    label_lib.set_label(store, req.id, 'debug')
    removed = label_lib.remove_label(store, req.id)
    assert removed is True
    assert label_lib.get_label(store, req.id) is None


def test_remove_label_not_found(store):
    result = label_lib.remove_label(store, 'ghost')
    assert result is False


def test_filter_by_label(store):
    r1 = _make_request(store, path='/a')
    r2 = _make_request(store, path='/b')
    r3 = _make_request(store, path='/c')
    label_lib.set_label(store, r1.id, 'error')
    label_lib.set_label(store, r3.id, 'error')
    label_lib.set_label(store, r2.id, 'info')
    results = label_lib.filter_by_label(store, 'error')
    ids = [r.id for r in results]
    assert r1.id in ids
    assert r3.id in ids
    assert r2.id not in ids


def test_list_all_labels(store):
    r1 = _make_request(store)
    r2 = _make_request(store)
    r3 = _make_request(store)
    label_lib.set_label(store, r1.id, 'error')
    label_lib.set_label(store, r2.id, 'error')
    label_lib.set_label(store, r3.id, 'info')
    counts = label_lib.list_all_labels(store)
    assert counts['error'] == 2
    assert counts['info'] == 1


def test_list_all_labels_empty(store):
    _make_request(store)
    counts = label_lib.list_all_labels(store)
    assert counts == {}
