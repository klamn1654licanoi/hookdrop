"""Per-request numeric scoring for prioritization and ranking."""

_scores = {}


def set_score(store, req_id, value):
    """Assign a numeric score to a request."""
    if not isinstance(value, (int, float)):
        raise ValueError("score must be a number")
    req = store.get(req_id)
    if req is None:
        raise KeyError(f"Request {req_id!r} not found")
    _scores[req_id] = value


def get_score(store, req_id):
    """Return the score for a request, or None if unset."""
    return _scores.get(req_id)


def remove_score(store, req_id):
    """Remove the score for a request."""
    _scores.pop(req_id, None)


def list_all_scores(store):
    """Return a dict of {req_id: score} for all scored requests still in the store."""
    valid_ids = {r.id for r in store.all()}
    return {k: v for k, v in _scores.items() if k in valid_ids}


def filter_by_min_score(store, min_score):
    """Return requests whose score is >= min_score."""
    valid_ids = {r.id for r in store.all()}
    matching_ids = [
        req_id
        for req_id, score in _scores.items()
        if score >= min_score and req_id in valid_ids
    ]
    return [store.get(req_id) for req_id in matching_ids if store.get(req_id) is not None]


def sort_by_score(store, descending=True):
    """Return all requests sorted by score. Unscored requests come last."""
    all_requests = store.all()
    scored = [(r, _scores.get(r.id)) for r in all_requests]
    scored_only = [(r, s) for r, s in scored if s is not None]
    unscored = [r for r, s in scored if s is None]
    scored_only.sort(key=lambda x: x[1], reverse=descending)
    return [r for r, _ in scored_only] + unscored


def clear_scores():
    """Clear all scores (useful for testing)."""
    _scores.clear()
