import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.scoring import (
    set_score, get_score, remove_score, list_all_scores,
    filter_by_min_score, sort_by_score, clear_scores
)


@pytest.fixture(autouse=True)
def reset_scores():
    clear_scores()
    yield
    clear_scores()


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store, path="/test", method="POST"):
    req = WebhookRequest(method=method, path=path, headers={}, body=b"")
    store.save(req)
    return req


def test_set_and_get_score(store):
    req = _make_request(store)
    set_score(store, req.id, 5.0)
    assert get_score(store, req.id) == 5.0


def test_set_score_not_found(store):
    with pytest.raises(KeyError):
        set_score(store, "nonexistent", 3)


def test_get_score_unset(store):
    req = _make_request(store)
    assert get_score(store, req.id) is None


def test_remove_score(store):
    req = _make_request(store)
    set_score(store, req.id, 9)
    remove_score(store, req.id)
    assert get_score(store, req.id) is None


def test_remove_score_nonexistent_is_safe(store):
    remove_score(store, "ghost")  # should not raise


def test_list_all_scores_empty(store):
    assert list_all_scores(store) == {}


def test_list_all_scores_with_entries(store):
    r1 = _make_request(store, path="/a")
    r2 = _make_request(store, path="/b")
    set_score(store, r1.id, 1)
    set_score(store, r2.id, 2)
    scores = list_all_scores(store)
    assert scores[r1.id] == 1
    assert scores[r2.id] == 2


def test_filter_by_min_score(store):
    r1 = _make_request(store, path="/low")
    r2 = _make_request(store, path="/high")
    set_score(store, r1.id, 2)
    set_score(store, r2.id, 8)
    results = filter_by_min_score(store, 5)
    ids = [r.id for r in results]
    assert r2.id in ids
    assert r1.id not in ids


def test_filter_by_min_score_no_match(store):
    req = _make_request(store)
    set_score(store, req.id, 1)
    assert filter_by_min_score(store, 10) == []


def test_sort_by_score_descending(store):
    r1 = _make_request(store, path="/a")
    r2 = _make_request(store, path="/b")
    r3 = _make_request(store, path="/c")
    set_score(store, r1.id, 3)
    set_score(store, r2.id, 9)
    set_score(store, r3.id, 1)
    sorted_reqs = sort_by_score(store, descending=True)
    scores = [get_score(store, r.id) for r in sorted_reqs if get_score(store, r.id) is not None]
    assert scores == sorted(scores, reverse=True)


def test_sort_by_score_unscored_last(store):
    r1 = _make_request(store, path="/scored")
    r2 = _make_request(store, path="/unscored")
    set_score(store, r1.id, 5)
    result = sort_by_score(store)
    assert result[0].id == r1.id
    assert result[-1].id == r2.id
