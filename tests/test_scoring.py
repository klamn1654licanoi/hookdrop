import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import scoring
from datetime import datetime


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture(autouse=True)
def reset_scores():
    scoring.clear_scores()
    yield
    scoring.clear_scores()


def _make_request(store: RequestStore, path: str = "/hook") -> WebhookRequest:
    req = WebhookRequest(
        method="POST",
        path=path,
        headers={"content-type": "application/json"},
        body=b'{"x": 1}',
        timestamp=datetime.utcnow().isoformat(),
    )
    store.save(req)
    return req


def test_set_and_get_score(store):
    req = _make_request(store)
    result = scoring.set_score(store, req.id, 7.5)
    assert result["score"] == 7.5
    assert scoring.get_score(store, req.id) == 7.5


def test_set_score_not_found(store):
    with pytest.raises(KeyError):
        scoring.set_score(store, "nonexistent", 5.0)


def test_get_score_unset(store):
    req = _make_request(store)
    assert scoring.get_score(store, req.id) is None


def test_get_score_not_found(store):
    with pytest.raises(KeyError):
        scoring.get_score(store, "ghost")


def test_remove_score(store):
    req = _make_request(store)
    scoring.set_score(store, req.id, 3.0)
    removed = scoring.remove_score(store, req.id)
    assert removed is True
    assert scoring.get_score(store, req.id) is None


def test_remove_score_not_set(store):
    req = _make_request(store)
    removed = scoring.remove_score(store, req.id)
    assert removed is False


def test_remove_score_not_found(store):
    with pytest.raises(KeyError):
        scoring.remove_score(store, "missing")


def test_list_all_scores_sorted(store):
    r1 = _make_request(store, "/a")
    r2 = _make_request(store, "/b")
    r3 = _make_request(store, "/c")
    scoring.set_score(store, r1.id, 1.0)
    scoring.set_score(store, r2.id, 9.0)
    scoring.set_score(store, r3.id, 5.0)
    scores = scoring.list_all_scores(store)
    assert scores[0]["score"] == 9.0
    assert scores[1]["score"] == 5.0
    assert scores[2]["score"] == 1.0


def test_filter_by_min_score(store):
    r1 = _make_request(store, "/low")
    r2 = _make_request(store, "/high")
    scoring.set_score(store, r1.id, 2.0)
    scoring.set_score(store, r2.id, 8.0)
    result = scoring.filter_by_min_score(store, 5.0)
    assert len(result) == 1
    assert result[0]["id"] == r2.id


def test_set_invalid_score(store):
    req = _make_request(store)
    with pytest.raises((ValueError, TypeError)):
        scoring.set_score(store, req.id, "high")  # type: ignore
