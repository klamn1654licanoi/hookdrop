"""Request scoring — assign and manage numeric scores for webhook requests."""

from hookdrop.storage import RequestStore

_scores: dict[str, float] = {}


def set_score(store: RequestStore, request_id: str, score: float) -> dict:
    """Assign a numeric score to a request."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found.")
    if not isinstance(score, (int, float)):
        raise ValueError("Score must be a numeric value.")
    _scores[request_id] = float(score)
    return {"id": request_id, "score": _scores[request_id]}


def get_score(store: RequestStore, request_id: str) -> float | None:
    """Return the score for a request, or None if unscored."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found.")
    return _scores.get(request_id)


def remove_score(store: RequestStore, request_id: str) -> bool:
    """Remove the score for a request. Returns True if removed."""
    if store.get(request_id) is None:
        raise KeyError(f"Request '{request_id}' not found.")
    if request_id in _scores:
        del _scores[request_id]
        return True
    return False


def list_all_scores(store: RequestStore) -> list[dict]:
    """Return all scored requests as a list of {id, score} dicts."""
    result = []
    for request_id, score in _scores.items():
        if store.get(request_id) is not None:
            result.append({"id": request_id, "score": score})
    return sorted(result, key=lambda x: x["score"], reverse=True)


def filter_by_min_score(store: RequestStore, min_score: float) -> list[dict]:
    """Return requests with a score >= min_score."""
    return [
        entry for entry in list_all_scores(store)
        if entry["score"] >= min_score
    ]


def clear_scores() -> None:
    """Remove all scores (used for testing / reset)."""
    _scores.clear()
