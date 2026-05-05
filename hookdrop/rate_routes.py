from flask import Blueprint, jsonify, request

from hookdrop.rate import rate_summary, rate_by_method, rate_by_path, rate_per_minute

_rate_bp = Blueprint("rate", __name__)
_store = None


def init_rate_routes(app, store):
    global _store
    _store = store
    app.register_blueprint(_rate_bp)


@_rate_bp.route("/rate/summary", methods=["GET"])
def summary():
    """Return rate summary. Optional ?window=N query param (seconds)."""
    try:
        window = int(request.args.get("window", 60))
    except ValueError:
        return jsonify({"error": "window must be an integer"}), 400
    if window <= 0:
        return jsonify({"error": "window must be positive"}), 400
    return jsonify(rate_summary(_store, window_seconds=window))


@_rate_bp.route("/rate/per-minute", methods=["GET"])
def per_minute():
    """Return simple requests-per-minute count (last 60s)."""
    return jsonify({"requests_per_minute": rate_per_minute(_store)})


@_rate_bp.route("/rate/by-method", methods=["GET"])
def by_method():
    """Return request counts grouped by method for the last window."""
    try:
        window = int(request.args.get("window", 60))
    except ValueError:
        return jsonify({"error": "window must be an integer"}), 400
    return jsonify(rate_by_method(_store, window_seconds=window))


@_rate_bp.route("/rate/by-path", methods=["GET"])
def by_path():
    """Return request counts grouped by path for the last window."""
    try:
        window = int(request.args.get("window", 60))
    except ValueError:
        return jsonify({"error": "window must be an integer"}), 400
    return jsonify(rate_by_path(_store, window_seconds=window))
