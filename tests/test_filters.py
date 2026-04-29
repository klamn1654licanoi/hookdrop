"""Tests for hookdrop request filtering."""

import pytest
from hookdrop.filters import (
    matches_method,
    matches_path,
    matches_header,
    matches_body,
    apply_filters,
)

SAMPLE_REQUEST = {
    "method": "POST",
    "path": "/webhooks/github",
    "headers": {"Content-Type": "application/json", "X-Hub-Signature": "sha1=abc"},
    "body": '{"action": "push", "ref": "refs/heads/main"}',
}


def test_matches_method_exact():
    assert matches_method(SAMPLE_REQUEST, "POST") is True


def test_matches_method_case_insensitive():
    assert matches_method(SAMPLE_REQUEST, "post") is True


def test_matches_method_no_filter():
    assert matches_method(SAMPLE_REQUEST, None) is True


def test_matches_method_wrong():
    assert matches_method(SAMPLE_REQUEST, "GET") is False


def test_matches_path_substring():
    assert matches_path(SAMPLE_REQUEST, "/webhooks") is True


def test_matches_path_exact():
    assert matches_path(SAMPLE_REQUEST, "/webhooks/github") is True


def test_matches_path_no_match():
    assert matches_path(SAMPLE_REQUEST, "/other") is False


def test_matches_path_no_filter():
    assert matches_path(SAMPLE_REQUEST, None) is True


def test_matches_header_key_only():
    assert matches_header(SAMPLE_REQUEST, "Content-Type", None) is True


def test_matches_header_key_and_value():
    assert matches_header(SAMPLE_REQUEST, "Content-Type", "application/json") is True


def test_matches_header_wrong_value():
    assert matches_header(SAMPLE_REQUEST, "Content-Type", "text/plain") is False


def test_matches_header_missing_key():
    assert matches_header(SAMPLE_REQUEST, "Authorization", None) is False


def test_matches_body_found():
    assert matches_body(SAMPLE_REQUEST, "push") is True


def test_matches_body_not_found():
    assert matches_body(SAMPLE_REQUEST, "pull_request") is False


def test_matches_body_no_filter():
    assert matches_body(SAMPLE_REQUEST, None) is True


def test_apply_filters_all_match():
    result = apply_filters(
        [SAMPLE_REQUEST],
        method="POST",
        path="/webhooks",
        header_key="Content-Type",
        header_value="application/json",
        body_contains="push",
    )
    assert len(result) == 1


def test_apply_filters_no_match():
    result = apply_filters([SAMPLE_REQUEST], method="DELETE")
    assert result == []


def test_apply_filters_empty_list():
    result = apply_filters([], method="POST")
    assert result == []


def test_apply_filters_no_filters():
    result = apply_filters([SAMPLE_REQUEST])
    assert len(result) == 1
