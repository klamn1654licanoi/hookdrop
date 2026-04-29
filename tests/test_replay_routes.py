import pytest
from unittest.mock import patch, MagicMock
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clear_store(store):
    store.clear()
    yield
    store.clear()


def _post_webhook(client):
    return client.post(
        "/webhook",
        json={"event": "ping"},
        headers={"X-Source": "test"},
    )


def test_replay_not_found(client):
    resp = client.post(
        "/requests/nonexistent/replay",
        json={"target_url": "http://example.com"},
    )
    assert resp.status_code == 404
    assert "not found" in resp.get_json()["error"].lower()


def test_replay_missing_target_url(client):
    _post_webhook(client)
    list_resp = client.get("/requests")
    request_id = list_resp.get_json()[0]["id"]

    resp = client.post(f"/requests/{request_id}/replay", json={})
    assert resp.status_code == 400
    assert "target_url" in resp.get_json()["error"]


def test_replay_success(client):
    _post_webhook(client)
    list_resp = client.get("/requests")
    request_id = list_resp.get_json()[0]["id"]

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text = '{"ok": true}'
    mock_response.url = "http://example.com/webhook"

    with patch("hookdrop.replay_routes.replay_request", return_value=mock_response):
        resp = client.post(
            f"/requests/{request_id}/replay",
            json={"target_url": "http://example.com/webhook"},
        )

    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status_code"] == 200
    assert data["url"] == "http://example.com/webhook"


def test_replay_upstream_error(client):
    _post_webhook(client)
    list_resp = client.get("/requests")
    request_id = list_resp.get_json()[0]["id"]

    with patch(
        "hookdrop.replay_routes.replay_request",
        side_effect=Exception("Connection refused"),
    ):
        resp = client.post(
            f"/requests/{request_id}/replay",
            json={"target_url": "http://localhost:9999/dead"},
        )

    assert resp.status_code == 502
    assert "Connection refused" in resp.get_json()["error"]
