"""Tests for the export module."""

import json
import pytest
from hookdrop.storage import WebhookRequest
from hookdrop import export


@pytest.fixture
def sample_request():
    return WebhookRequest(
        id="abc123",
        method="POST",
        path="/webhook",
        headers={"Content-Type": "application/json", "X-Token": "secret"},
        body='{"event": "ping"}',
        query_string="foo=bar",
        timestamp="2024-01-01T00:00:00",
    )


@pytest.fixture
def get_request():
    return WebhookRequest(
        id="def456",
        method="GET",
        path="/ping",
        headers={"Accept": "*/*"},
        body="",
        query_string="",
        timestamp="2024-01-01T00:01:00",
    )


def test_to_json_single(sample_request):
    result = export.to_json([sample_request])
    data = json.loads(result)
    assert len(data) == 1
    assert data[0]["id"] == "abc123"
    assert data[0]["method"] == "POST"


def test_to_json_empty():
    result = export.to_json([])
    assert json.loads(result) == []


def test_to_json_multiple(sample_request, get_request):
    result = export.to_json([sample_request, get_request])
    data = json.loads(result)
    assert len(data) == 2


def test_to_curl_post_basic(sample_request):
    cmd = export.to_curl(sample_request, target_url="http://example.com/webhook")
    assert "curl" in cmd
    assert "-X" in cmd
    assert "POST" in cmd
    assert "http://example.com/webhook" in cmd


def test_to_curl_includes_headers(sample_request):
    cmd = export.to_curl(sample_request, target_url="http://example.com/webhook")
    assert "X-Token" in cmd
    assert "Content-Type" in cmd


def test_to_curl_strips_host_and_content_length():
    req = WebhookRequest(
        id="x",
        method="POST",
        path="/test",
        headers={"Host": "old.host", "Content-Length": "42", "X-Custom": "yes"},
        body="data",
        query_string="",
        timestamp="2024-01-01T00:00:00",
    )
    cmd = export.to_curl(req, target_url="http://new.host/test")
    assert "Host" not in cmd
    assert "Content-Length" not in cmd
    assert "X-Custom" in cmd


def test_to_curl_includes_body(sample_request):
    cmd = export.to_curl(sample_request, target_url="http://example.com/webhook")
    assert "--data-raw" in cmd
    assert "ping" in cmd


def test_to_curl_get_no_body(get_request):
    cmd = export.to_curl(get_request, target_url="http://example.com/ping")
    assert "--data-raw" not in cmd


def test_to_curl_default_url(sample_request):
    cmd = export.to_curl(sample_request)
    assert "localhost:9000" in cmd
    assert "/webhook" in cmd


def test_to_curl_all(sample_request, get_request):
    result = export.to_curl_all([sample_request, get_request], target_url="http://example.com")
    lines = result.strip().split("\n")
    assert len(lines) == 2
    assert all(line.startswith("curl") for line in lines)
