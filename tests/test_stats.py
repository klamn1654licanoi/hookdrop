import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.stats import compute_stats, most_common_method, most_common_path


@pytest.fixture
def store():
    return RequestStore()


def _make_request(method="POST", path="/hook", status_code=200):
    return WebhookRequest(
        method=method,
        path=path,
        headers={"Content-Type": "application/json"},
        body="{}",
        status_code=status_code,
    )


def test_compute_stats_empty(store):
    result = compute_stats(store)
    assert result["total"] == 0
    assert result["by_method"] == {}
    assert result["by_path"] == {}
    assert result["by_status"] == {}


def test_compute_stats_single(store):
    store.save(_make_request("POST", "/hook", 200))
    result = compute_stats(store)
    assert result["total"] == 1
    assert result["by_method"] == {"POST": 1}
    assert result["by_path"] == {"/hook": 1}
    assert result["by_status"] == {"200": 1}


def test_compute_stats_multiple_methods(store):
    store.save(_make_request("POST", "/a"))
    store.save(_make_request("GET", "/b"))
    store.save(_make_request("POST", "/a"))
    result = compute_stats(store)
    assert result["total"] == 3
    assert result["by_method"]["POST"] == 2
    assert result["by_method"]["GET"] == 1


def test_compute_stats_method_case_normalised(store):
    store.save(_make_request("post", "/x"))
    result = compute_stats(store)
    assert "POST" in result["by_method"]


def test_most_common_method_empty(store):
    assert most_common_method(store) is None


def test_most_common_method(store):
    store.save(_make_request("GET", "/a"))
    store.save(_make_request("POST", "/b"))
    store.save(_make_request("POST", "/c"))
    assert most_common_method(store) == "POST"


def test_most_common_path_empty(store):
    assert most_common_path(store) is None


def test_most_common_path(store):
    store.save(_make_request("POST", "/alpha"))
    store.save(_make_request("GET", "/alpha"))
    store.save(_make_request("POST", "/beta"))
    assert most_common_path(store) == "/alpha"
