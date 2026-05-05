"""Snapshot support: save and restore named snapshots of the request store."""

from typing import Dict, List, Optional
from hookdrop.storage import RequestStore, WebhookRequest

_snapshots: Dict[str, List[dict]] = {}


def save_snapshot(store: RequestStore, name: str) -> int:
    """Save the current store contents under the given name. Returns count saved."""
    _snapshots[name] = [req.to_dict() for req in store.all()]
    return len(_snapshots[name])


def load_snapshot(store: RequestStore, name: str) -> Optional[int]:
    """Restore a named snapshot into the store. Returns count loaded, or None if not found."""
    if name not in _snapshots:
        return None
    store.clear()
    for data in _snapshots[name]:
        req = WebhookRequest(
            id=data["id"],
            method=data["method"],
            path=data["path"],
            headers=data["headers"],
            body=data["body"],
            timestamp=data["timestamp"],
        )
        store.save(req)
    return len(_snapshots[name])


def list_snapshots() -> List[str]:
    """Return names of all saved snapshots."""
    return list(_snapshots.keys())


def delete_snapshot(name: str) -> bool:
    """Delete a named snapshot. Returns True if it existed."""
    if name in _snapshots:
        del _snapshots[name]
        return True
    return False


def get_snapshot(name: str) -> Optional[List[dict]]:
    """Return raw snapshot data by name, or None if not found."""
    return _snapshots.get(name)


def clear_all_snapshots() -> None:
    """Remove all snapshots (useful for testing)."""
    _snapshots.clear()
