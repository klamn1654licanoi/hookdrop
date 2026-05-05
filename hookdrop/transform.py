"""Request transformation utilities for modifying replayed or forwarded requests."""

from typing import Optional
from hookdrop.storage import WebhookRequest, RequestStore


def set_header(store: RequestStore, request_id: str, key: str, value: str) -> Optional[WebhookRequest]:
    """Add or overwrite a header on a stored request."""
    req = store.get(request_id)
    if req is None:
        return None
    req.headers[key] = value
    return req


def remove_header(store: RequestStore, request_id: str, key: str) -> Optional[WebhookRequest]:
    """Remove a header from a stored request if it exists."""
    req = store.get(request_id)
    if req is None:
        return None
    req.headers.pop(key, None)
    return req


def rewrite_body(store: RequestStore, request_id: str, new_body: str) -> Optional[WebhookRequest]:
    """Replace the body of a stored request."""
    req = store.get(request_id)
    if req is None:
        return None
    req.body = new_body
    return req


def rewrite_path(store: RequestStore, request_id: str, new_path: str) -> Optional[WebhookRequest]:
    """Replace the path of a stored request."""
    req = store.get(request_id)
    if req is None:
        return None
    req.path = new_path
    return req


def get_transforms(req: WebhookRequest) -> dict:
    """Return a summary of mutable fields for a request."""
    return {
        "id": req.id,
        "path": req.path,
        "headers": dict(req.headers),
        "body": req.body,
    }
