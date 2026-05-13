"""Request sequence detection — identify ordered patterns across captured requests."""

from typing import List, Optional, Dict
from hookdrop.storage import RequestStore

_sequences: Dict[str, List[str]] = {}  # name -> [request_id, ...]


def define_sequence(name: str, request_ids: List[str]) -> Dict:
    """Define a named sequence from an ordered list of request IDs."""
    if not name:
        raise ValueError("Sequence name must not be empty")
    if not request_ids:
        raise ValueError("Sequence must contain at least one request ID")
    _sequences[name] = list(request_ids)
    return {"name": name, "request_ids": _sequences[name]}


def get_sequence(name: str) -> Optional[Dict]:
    """Retrieve a named sequence by name."""
    ids = _sequences.get(name)
    if ids is None:
        return None
    return {"name": name, "request_ids": ids}


def delete_sequence(name: str) -> bool:
    """Delete a named sequence. Returns True if it existed."""
    if name in _sequences:
        del _sequences[name]
        return True
    return False


def list_sequences() -> List[Dict]:
    """List all defined sequences."""
    return [{"name": n, "request_ids": ids} for n, ids in _sequences.items()]


def clear_sequences() -> None:
    """Remove all sequences."""
    _sequences.clear()


def validate_sequence(name: str, store: RequestStore) -> Dict:
    """Check whether all requests in the sequence exist in the store.

    Returns a report with 'valid', 'missing', and 'found' keys.
    """
    seq = get_sequence(name)
    if seq is None:
        raise KeyError(f"Sequence '{name}' not found")

    found = []
    missing = []
    for rid in seq["request_ids"]:
        if store.get(rid) is not None:
            found.append(rid)
        else:
            missing.append(rid)

    return {
        "name": name,
        "valid": len(missing) == 0,
        "found": found,
        "missing": missing,
        "total": len(seq["request_ids"]),
    }
