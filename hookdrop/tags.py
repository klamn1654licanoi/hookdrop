"""Tag management for webhook requests — assign, remove, and filter by tags."""

from typing import List, Optional
from hookdrop.storage import RequestStore


def add_tag(store: RequestStore, request_id: str, tag: str) -> bool:
    """Add a tag to a request. Returns True if successful, False if not found."""
    req = store.get(request_id)
    if req is None:
        return False
    tags = req.meta.get("tags", [])
    if tag not in tags:
        tags.append(tag)
    req.meta["tags"] = tags
    return True


def remove_tag(store: RequestStore, request_id: str, tag: str) -> bool:
    """Remove a tag from a request. Returns True if successful, False if not found."""
    req = store.get(request_id)
    if req is None:
        return False
    tags = req.meta.get("tags", [])
    if tag in tags:
        tags.remove(tag)
    req.meta["tags"] = tags
    return True


def get_tags(store: RequestStore, request_id: str) -> Optional[List[str]]:
    """Return tags for a request, or None if request not found."""
    req = store.get(request_id)
    if req is None:
        return None
    return req.meta.get("tags", [])


def filter_by_tag(store: RequestStore, tag: str) -> list:
    """Return all requests that have the given tag."""
    results = []
    for req in store.all():
        if tag in req.meta.get("tags", []):
            results.append(req)
    return results


def list_all_tags(store: RequestStore) -> List[str]:
    """Return a sorted list of all unique tags across all requests."""
    tags = set()
    for req in store.all():
        for tag in req.meta.get("tags", []):
            tags.add(tag)
    return sorted(tags)
