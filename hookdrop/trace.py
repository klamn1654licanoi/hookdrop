"""Request tracing — attach trace IDs and track propagation chains."""

from __future__ import annotations

import uuid
from typing import Optional

from hookdrop.storage import RequestStore

# trace_id -> list of request IDs in order
_traces: dict[str, list[str]] = {}
# request_id -> trace_id
_request_trace: dict[str, str] = {}


def start_trace(trace_id: Optional[str] = None) -> str:
    """Create a new trace, returning its ID."""
    if trace_id is None:
        trace_id = str(uuid.uuid4())
    if trace_id not in _traces:
        _traces[trace_id] = []
    return trace_id


def attach_trace(store: RequestStore, request_id: str, trace_id: str) -> bool:
    """Attach a request to a trace. Returns False if request not found."""
    req = store.get(request_id)
    if req is None:
        return False
    trace_id = start_trace(trace_id)
    if request_id not in _traces[trace_id]:
        _traces[trace_id].append(request_id)
    _request_trace[request_id] = trace_id
    return True


def detach_trace(request_id: str) -> bool:
    """Remove a request from its trace. Returns False if not traced."""
    trace_id = _request_trace.pop(request_id, None)
    if trace_id is None:
        return False
    if trace_id in _traces and request_id in _traces[trace_id]:
        _traces[trace_id].remove(request_id)
    return True


def get_trace_for_request(request_id: str) -> Optional[str]:
    """Return the trace ID for a given request, or None."""
    return _request_trace.get(request_id)


def get_trace(trace_id: str) -> Optional[list[str]]:
    """Return ordered list of request IDs in a trace, or None if unknown."""
    return _traces.get(trace_id)


def list_traces() -> dict[str, list[str]]:
    """Return all traces."""
    return dict(_traces)


def delete_trace(trace_id: str) -> bool:
    """Delete a trace and detach all its requests."""
    request_ids = _traces.pop(trace_id, None)
    if request_ids is None:
        return False
    for rid in request_ids:
        _request_trace.pop(rid, None)
    return True


def clear_traces() -> None:
    """Remove all traces."""
    _traces.clear()
    _request_trace.clear()
