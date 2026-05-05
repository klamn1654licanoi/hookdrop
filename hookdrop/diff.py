"""Diff utilities for comparing two webhook requests."""

from typing import Optional
from hookdrop.storage import WebhookRequest


def diff_headers(a: WebhookRequest, b: WebhookRequest) -> dict:
    """Return added, removed, and changed headers between two requests."""
    a_headers = {k.lower(): v for k, v in a.headers.items()}
    b_headers = {k.lower(): v for k, v in b.headers.items()}

    added = {k: b_headers[k] for k in b_headers if k not in a_headers}
    removed = {k: a_headers[k] for k in a_headers if k not in b_headers}
    changed = {
        k: {"from": a_headers[k], "to": b_headers[k]}
        for k in a_headers
        if k in b_headers and a_headers[k] != b_headers[k]
    }

    return {"added": added, "removed": removed, "changed": changed}


def diff_body(a: WebhookRequest, b: WebhookRequest) -> dict:
    """Return a simple body diff between two requests."""
    body_a = a.body or ""
    body_b = b.body or ""

    if body_a == body_b:
        return {"changed": False, "from": body_a, "to": body_b}

    return {"changed": True, "from": body_a, "to": body_b}


def diff_requests(a: WebhookRequest, b: WebhookRequest) -> dict:
    """Produce a full diff summary between two WebhookRequests."""
    return {
        "id_a": a.id,
        "id_b": b.id,
        "method": {
            "changed": a.method != b.method,
            "from": a.method,
            "to": b.method,
        },
        "path": {
            "changed": a.path != b.path,
            "from": a.path,
            "to": b.path,
        },
        "headers": diff_headers(a, b),
        "body": diff_body(a, b),
    }
