"""Unit tests for hookdrop/trace.py."""

import pytest
from hookdrop.storage import RequestStore
from hookdrop import trace as trace_module
from hookdrop.trace import (
    start_trace, attach_trace, detach_trace,
    get_trace_for_request, get_trace, list_traces,
    delete_trace, clear_traces,
)


@pytest.fixture(autouse=True)
def reset():
    clear_traces()
    yield
    clear_traces()


@pytest.fixture()
def store():
    s = RequestStore()
    return s


def _make_request(store):
    from hookdrop.storage import WebhookRequest
    import datetime
    req = WebhookRequest(
        id="req-1",
        method="POST",
        path="/hook",
        headers={},
        body="",
        timestamp=datetime.datetime.utcnow().isoformat(),
        query_string="",
        source_ip="127.0.0.1",
    )
    store.save(req)
    return req


def test_start_trace_generates_id():
    tid = start_trace()
    assert isinstance(tid, str)
    assert len(tid) > 0


def test_start_trace_custom_id():
    tid = start_trace("my-trace")
    assert tid == "my-trace"
    assert "my-trace" in list_traces()


def test_attach_trace_success(store):
    req = _make_request(store)
    tid = start_trace("t1")
    result = attach_trace(store, req.id, tid)
    assert result is True
    assert req.id in get_trace("t1")
    assert get_trace_for_request(req.id) == "t1"


def test_attach_trace_not_found(store):
    result = attach_trace(store, "nonexistent", "t1")
    assert result is False


def test_attach_no_duplicates(store):
    req = _make_request(store)
    attach_trace(store, req.id, "t1")
    attach_trace(store, req.id, "t1")
    assert get_trace("t1").count(req.id) == 1


def test_detach_trace(store):
    req = _make_request(store)
    attach_trace(store, req.id, "t1")
    ok = detach_trace(req.id)
    assert ok is True
    assert get_trace_for_request(req.id) is None
    assert req.id not in get_trace("t1")


def test_detach_not_traced():
    ok = detach_trace("unknown")
    assert ok is False


def test_delete_trace(store):
    req = _make_request(store)
    attach_trace(store, req.id, "t1")
    deleted = delete_trace("t1")
    assert deleted is True
    assert get_trace("t1") is None
    assert get_trace_for_request(req.id) is None


def test_delete_trace_not_found():
    assert delete_trace("ghost") is False


def test_list_traces_empty():
    assert list_traces() == {}


def test_list_traces_multiple():
    start_trace("a")
    start_trace("b")
    traces = list_traces()
    assert "a" in traces
    assert "b" in traces
