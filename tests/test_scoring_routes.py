import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.scoring_routes import init_scoring_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_scoring_routes(app, store)
    app.config["TESTING"] = True
    return app.test_client()


def _post_webhook(client, path="/webhook", method="POST", body=b"hello"):
    return client.open(path, method=method, data=body)


def test_get_score_not_found(client):
    res = client.get("/requests/missing/score")
    assert res.status_code == 404


def test_set_and_get_score(client, store):
    _post_webhook(client)
    req_id = store.all()[0].id

    res = client.put(f"/requests/{req_id}/score", json={"score": 7.5})
    assert res.status_code == 200
    assert res.get_json()["score"] == 7.5

    res = client.get(f"/requests/{req_id}/score")
    assert res.status_code == 200
    assert res.get_json()["score"] == 7.5


def test_set_score_invalid(client, store):
    _post_webhook(client)
    req_id = store.all()[0].id

    res = client.put(f"/requests/{req_id}/score", json={"score": "high"})
    assert res.status_code == 400


def test_set_score_missing_body(client, store):
    _post_webhook(client)
    req_id = store.all()[0].id

    res = client.put(f"/requests/{req_id}/score", json={})
    assert res.status_code == 400


def test_delete_score(client, store):
    _post_webhook(client)
    req_id = store.all()[0].id

    client.put(f"/requests/{req_id}/score", json={"score": 5})
    res = client.delete(f"/requests/{req_id}/score")
    assert res.status_code == 200
    assert res.get_json()["score"] is None


def test_all_scores_empty(client):
    res = client.get("/scores")
    assert res.status_code == 200
    assert res.get_json() == {}


def test_all_scores_after_set(client, store):
    _post_webhook(client)
    req_id = store.all()[0].id
    client.put(f"/requests/{req_id}/score", json={"score": 3})

    res = client.get("/scores")
    data = res.get_json()
    assert req_id in data
    assert data[req_id] == 3


def test_filter_by_min_score(client, store):
    _post_webhook(client, path="/a")
    _post_webhook(client, path="/b")
    ids = [r.id for r in store.all()]

    client.put(f"/requests/{ids[0]}/score", json={"score": 2})
    client.put(f"/requests/{ids[1]}/score", json={"score": 8})

    res = client.get("/scores/filter?min=5")
    assert res.status_code == 200
    results = res.get_json()
    result_ids = [r["id"] for r in results]
    assert ids[1] in result_ids
    assert ids[0] not in result_ids


def test_filter_by_min_score_invalid(client):
    res = client.get("/scores/filter?min=abc")
    assert res.status_code == 400
