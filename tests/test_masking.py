"""Tests for hookdrop.masking."""

import pytest
from hookdrop.masking import (
    add_mask_rule,
    remove_mask_rule,
    list_mask_rules,
    clear_mask_rules,
    mask_headers,
    mask_body,
    mask_request,
    DEFAULT_MASK,
)


@pytest.fixture(autouse=True)
def reset_rules():
    clear_mask_rules()
    yield
    clear_mask_rules()


def test_add_and_list_rule():
    add_mask_rule("authorization")
    rules = list_mask_rules()
    assert "authorization" in rules
    assert rules["authorization"] == DEFAULT_MASK


def test_add_rule_custom_mask():
    add_mask_rule("x-api-key", mask="[REDACTED]")
    assert list_mask_rules()["x-api-key"] == "[REDACTED]"


def test_remove_rule_existing():
    add_mask_rule("authorization")
    result = remove_mask_rule("authorization")
    assert result is True
    assert "authorization" not in list_mask_rules()


def test_remove_rule_missing():
    result = remove_mask_rule("nonexistent")
    assert result is False


def test_clear_mask_rules():
    add_mask_rule("authorization")
    add_mask_rule("x-api-key")
    clear_mask_rules()
    assert list_mask_rules() == {}


def test_mask_headers_matching_field():
    add_mask_rule("authorization")
    headers = {"Authorization": "Bearer secret-token", "Content-Type": "application/json"}
    result = mask_headers(headers)
    assert result["Authorization"] == DEFAULT_MASK
    assert result["Content-Type"] == "application/json"


def test_mask_headers_no_rules():
    headers = {"Authorization": "Bearer secret", "X-Custom": "value"}
    result = mask_headers(headers)
    assert result == headers


def test_mask_headers_case_insensitive():
    add_mask_rule("x-api-key")
    headers = {"X-Api-Key": "my-secret-key"}
    result = mask_headers(headers)
    assert result["X-Api-Key"] == DEFAULT_MASK


def test_mask_body_replaces_field():
    add_mask_rule("password")
    body = '{"username": "alice", "password": "supersecret"}'
    result = mask_body(body)
    assert DEFAULT_MASK in result
    assert "supersecret" not in result
    assert "alice" in result


def test_mask_body_no_match():
    add_mask_rule("password")
    body = '{"username": "alice"}'
    result = mask_body(body)
    assert result == body


def test_mask_body_no_rules():
    body = '{"password": "secret"}'
    result = mask_body(body)
    assert result == body


def test_mask_request_full():
    add_mask_rule("authorization")
    add_mask_rule("token")
    req = {
        "id": "abc123",
        "method": "POST",
        "headers": {"Authorization": "Bearer xyz", "Content-Type": "application/json"},
        "body": '{"token": "my-secret", "action": "login"}',
    }
    result = mask_request(req)
    assert result["headers"]["Authorization"] == DEFAULT_MASK
    assert result["headers"]["Content-Type"] == "application/json"
    assert "my-secret" not in result["body"]
    assert "login" in result["body"]
    # Original should be unchanged
    assert req["headers"]["Authorization"] == "Bearer xyz"
