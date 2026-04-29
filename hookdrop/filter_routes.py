"""Flask routes for filtered request inspection in hookdrop."""

from flask import Blueprint, request, jsonify
from hookdrop.storage import RequestStore
from hookdrop.filters import apply_filters

filter_bp = Blueprint("filters", __name__)
_store: RequestStore = None


def init_filter_routes(store: RequestStore) -> Blueprint:
    """Bind a RequestStore instance to the filter blueprint."""
    global _store
    _store = store
    return filter_bp


@filter_bp.route("/requests/filter", methods=["GET"])
def filter_requests():
    """Return stored requests matching the provided query parameters.

    Query params:
        method      - HTTP method (GET, POST, ...)
        path        - substring to match against request path
        header_key  - header name to require
        header_value - expected value for header_key (optional)
        body        - substring to search for in request body
    """
    method = request.args.get("method")
    path = request.args.get("path")
    header_key = request.args.get("header_key")
    header_value = request.args.get("header_value")
    body_contains = request.args.get("body")

    all_requests = [r.to_dict() for r in _store.all()]
    filtered = apply_filters(
        all_requests,
        method=method,
        path=path,
        header_key=header_key,
        header_value=header_value,
        body_contains=body_contains,
    )
    return jsonify({"count": len(filtered), "requests": filtered})
