"""Request deduplication — detect and manage duplicate webhook requests."""

import hashlib
import json
from hookdrop.storage import RequestStore

# Maps fingerprint -> list of request IDs
_fingerprints: dict[str, list[str]] = {}


def _fingerprint(request) -> str:
    """Compute a fingerprint from method, path, headers, and body."""
    key = {
        "method": request.method.upper(),
        "path": request.path,
        "body": request.body,
        "headers": {k.lower(): v for k, v in sorted(request.headers.items())},
    }
    raw = json.dumps(key, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def register_request(store: RequestStore, request_id: str) -> str:
    """Register a request and return its fingerprint."""
    req = store.get(request_id)
    if req is None:
        raise KeyError(f"Request '{request_id}' not found.")
    fp = _fingerprint(req)
    _fingerprints.setdefault(fp, [])
    if request_id not in _fingerprints[fp]:
        _fingerprints[fp].append(request_id)
    return fp


def is_duplicate(store: RequestStore, request_id: str) -> bool:
    """Return True if the request shares a fingerprint with another request."""
    req = store.get(request_id)
    if req is None:
        raise KeyError(f"Request '{request_id}' not found.")
    fp = _fingerprint(req)
    ids = _fingerprints.get(fp, [])
    return len(ids) > 1


def get_duplicates(store: RequestStore, request_id: str) -> list[str]:
    """Return all request IDs that are duplicates of the given request."""
    req = store.get(request_id)
    if req is None:
        raise KeyError(f"Request '{request_id}' not found.")
    fp = _fingerprint(req)
    ids = _fingerprints.get(fp, [])
    return [rid for rid in ids if rid != request_id]


def list_all_duplicates() -> dict[str, list[str]]:
    """Return all fingerprint groups that have more than one request."""
    return {fp: ids for fp, ids in _fingerprints.items() if len(ids) > 1}


def clear_dedup() -> None:
    """Clear all stored fingerprints."""
    _fingerprints.clear()
