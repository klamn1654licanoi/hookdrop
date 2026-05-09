"""Unit tests for hookdrop.redaction."""

import pytest

from hookdrop import redaction


@pytest.fixture(autouse=True)
def reset_rules():
    redaction.clear_rules()
    yield
    redaction.clear_rules()


def test_add_and_list_rule():
    redaction.add_rule("Authorization")
    rules = redaction.list_rules()
    assert "authorization" in rules
    assert rules["authorization"] == ""


def test_add_rule_with_pattern():
    redaction.add_rule("X-Secret", r"\bsecret\b")
    assert redaction.list_rules()["x-secret"] == r"\bsecret\b"


def test_remove_rule_existing():
    redaction.add_rule("Authorization")
    assert redaction.remove_rule("Authorization") is True
    assert "authorization" not in redaction.list_rules()


def test_remove_rule_missing():
    assert redaction.remove_rule("nonexistent") is False


def test_redact_headers_full():
    redaction.add_rule("Authorization")
    headers = {"Authorization": "Bearer abc123", "Content-Type": "application/json"}
    result = redaction.redact_headers(headers)
    assert result["Authorization"] == "[REDACTED]"
    assert result["Content-Type"] == "application/json"


def test_redact_headers_with_pattern():
    redaction.add_rule("X-Token", r"tok_[a-z0-9]+")
    headers = {"X-Token": "prefix tok_abc999 suffix"}
    result = redaction.redact_headers(headers)
    assert "[REDACTED]" in result["X-Token"]
    assert "prefix" in result["X-Token"]


def test_redact_body_json_key():
    redaction.add_rule("password")
    body = '{"username": "alice", "password": "s3cr3t"}'
    result = redaction.redact_body(body)
    assert "[REDACTED]" in result
    assert "s3cr3t" not in result


def test_redact_body_with_pattern():
    redaction.add_rule("card", r"\d{16}")
    body = "card number is 1234567890123456 end"
    result = redaction.redact_body(body)
    assert "[REDACTED]" in result
    assert "1234567890123456" not in result


def test_apply_redaction_full():
    redaction.add_rule("Authorization")
    req = {
        "id": "abc",
        "headers": {"Authorization": "Bearer xyz", "Host": "localhost"},
        "body": "hello",
    }
    out = redaction.apply_redaction(req)
    assert out["headers"]["Authorization"] == "[REDACTED]"
    assert out["headers"]["Host"] == "localhost"
    assert out["body"] == "hello"
    assert out["id"] == "abc"


def test_clear_rules():
    redaction.add_rule("Authorization")
    redaction.add_rule("X-Api-Key")
    redaction.clear_rules()
    assert redaction.list_rules() == {}
