from typing import List, Optional
from hookdrop.storage import WebhookRequest, RequestStore


def search_requests(
    store: RequestStore,
    query: str,
    fields: Optional[List[str]] = None,
) -> List[WebhookRequest]:
    """
    Search webhook requests by a query string across specified fields.
    Defaults to searching method, path, headers, and body.
    """
    if fields is None:
        fields = ["method", "path", "headers", "body"]

    query_lower = query.lower()
    results = []

    for req in store.all():
        if _request_matches(req, query_lower, fields):
            results.append(req)

    return results


def _request_matches(req: WebhookRequest, query: str, fields: List[str]) -> bool:
    if "method" in fields:
        if query in req.method.lower():
            return True

    if "path" in fields:
        if query in req.path.lower():
            return True

    if "headers" in fields:
        for key, value in req.headers.items():
            if query in key.lower() or query in value.lower():
                return True

    if "body" in fields:
        body = req.body or ""
        if query in body.lower():
            return True

    return False


def search_by_header_value(store: RequestStore, header_name: str, value: str) -> List[WebhookRequest]:
    """Find requests where a specific header matches a given value (case-insensitive)."""
    name_lower = header_name.lower()
    value_lower = value.lower()
    return [
        req for req in store.all()
        if any(
            k.lower() == name_lower and value_lower in v.lower()
            for k, v in req.headers.items()
        )
    ]
