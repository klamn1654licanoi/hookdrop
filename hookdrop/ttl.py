"""TTL (time-to-live) management for webhook requests."""

from datetime import datetime, timedelta
from typing import List, Optional
from hookdrop.storage import RequestStore, WebhookRequest


def is_expired(request: WebhookRequest, ttl_seconds: int) -> bool:
    """Return True if the request is older than ttl_seconds."""
    age = datetime.utcnow() - request.timestamp
    return age.total_seconds() > ttl_seconds


def expire_requests(store: RequestStore, ttl_seconds: int) -> List[str]:
    """Remove requests older than ttl_seconds. Returns list of removed IDs."""
    removed = []
    with store.lock:
        to_remove = [
            req for req in store.requests
            if is_expired(req, ttl_seconds)
        ]
        for req in to_remove:
            store.requests.remove(req)
            removed.append(req.id)
    return removed


def get_expiry_time(request: WebhookRequest, ttl_seconds: int) -> datetime:
    """Return the datetime when this request will expire."""
    return request.timestamp + timedelta(seconds=ttl_seconds)


def seconds_until_expiry(request: WebhookRequest, ttl_seconds: int) -> float:
    """Return seconds remaining before expiry. Negative means already expired."""
    expiry = get_expiry_time(request, ttl_seconds)
    return (expiry - datetime.utcnow()).total_seconds()


def ttl_summary(store: RequestStore, ttl_seconds: int) -> dict:
    """Return a summary of request TTL status."""
    with store.lock:
        requests = list(store.requests)

    expired_count = sum(1 for r in requests if is_expired(r, ttl_seconds))
    active_count = len(requests) - expired_count

    return {
        "total": len(requests),
        "active": active_count,
        "expired": expired_count,
        "ttl_seconds": ttl_seconds,
    }
