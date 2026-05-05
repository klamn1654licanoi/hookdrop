from typing import Optional
from hookdrop.storage import RequestStore


def set_label(store: RequestStore, request_id: str, label: str) -> bool:
    """Set a color/category label on a request. Returns False if not found."""
    req = store.get(request_id)
    if req is None:
        return False
    if not hasattr(req, 'meta') or req.meta is None:
        req.meta = {}
    req.meta['label'] = label.strip().lower()
    return True


def get_label(store: RequestStore, request_id: str) -> Optional[str]:
    """Get the label for a request, or None if not set."""
    req = store.get(request_id)
    if req is None or not hasattr(req, 'meta') or req.meta is None:
        return None
    return req.meta.get('label')


def remove_label(store: RequestStore, request_id: str) -> bool:
    """Remove the label from a request. Returns False if not found."""
    req = store.get(request_id)
    if req is None or not hasattr(req, 'meta') or req.meta is None:
        return False
    if 'label' in req.meta:
        del req.meta['label']
        return True
    return False


def filter_by_label(store: RequestStore, label: str) -> list:
    """Return all requests that have a specific label."""
    label = label.strip().lower()
    result = []
    for req in store.all():
        meta = getattr(req, 'meta', None) or {}
        if meta.get('label') == label:
            result.append(req)
    return result


def list_all_labels(store: RequestStore) -> dict:
    """Return a mapping of label -> count across all requests."""
    counts: dict = {}
    for req in store.all():
        meta = getattr(req, 'meta', None) or {}
        label = meta.get('label')
        if label:
            counts[label] = counts.get(label, 0) + 1
    return counts
