import pytest
from unittest.mock import MagicMock, patch
from hookdrop.storage import WebhookRequest
from hookdrop.replay import build_replay_request, replay_request
import httpx


SAMPLE_REQUEST = WebhookRequest(
    id="abc-123",
    method="POST",
    path="/webhook",
    headers={"Content-Type": "application/json", "Host": "localhost"},
    body='{"event": "push"}',
    query_string="",
)


def test_build_replay_request_basic():
    result = build_replay_request(SAMPLE_REQUEST, "http://example.com/hook")
    assert result["method"] == "POST"
    assert result["url"] == "http://example.com/hook"
    assert "Content-Type" in result["headers"]
    assert result["content"] == b'{"event": "push"}'


def test_build_replay_request_strips_host_header():
    result = build_replay_request(SAMPLE_REQUEST, "http://example.com/hook")
    assert "Host" not in result["headers"]
    assert "host" not in result["headers"]


def test_build_replay_request_strips_content_length():
    req = WebhookRequest(
        id="xyz",
        method="POST",
        path="/hook",
        headers={"Content-Length": "17", "X-Custom": "value"},
        body="hello",
        query_string="",
    )
    result = build_replay_request(req, "http://target.local/")
    assert "Content-Length" not in result["headers"]
    assert result["headers"].get("X-Custom") == "value"


@patch("hookdrop.replay.httpx.Client")
def test_replay_request_success(mock_client_cls):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"x-powered-by": "flask"}
    mock_response.text = "OK"

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.request.return_value = mock_response
    mock_client_cls.return_value = mock_client

    result = replay_request(SAMPLE_REQUEST, "http://example.com/hook")

    assert result["status_code"] == 200
    assert result["response_body"] == "OK"
    assert result["error"] is None
    assert result["request_id"] == "abc-123"


@patch("hookdrop.replay.httpx.Client")
def test_replay_request_timeout(mock_client_cls):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.request.side_effect = httpx.TimeoutException("timed out")
    mock_client_cls.return_value = mock_client

    result = replay_request(SAMPLE_REQUEST, "http://example.com/hook")

    assert result["status_code"] is None
    assert "timed out" in result["error"]


@patch("hookdrop.replay.httpx.Client")
def test_replay_request_connection_error(mock_client_cls):
    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    mock_client.request.side_effect = httpx.RequestError("connection refused")
    mock_client_cls.return_value = mock_client

    result = replay_request(SAMPLE_REQUEST, "http://example.com/hook")

    assert result["status_code"] is None
    assert "connection refused" in result["error"]
    assert result["request_id"] == "abc-123"
