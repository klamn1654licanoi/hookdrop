"""Routes for TTL management of webhook requests."""

from flask import Blueprint, jsonify, request, current_app
from hookdrop.ttl import expire_requests, ttl_summary, seconds_until_expiry

DEFAULT_TTL = 3600  # 1 hour


def init_ttl_routes(app, store):
    bp = Blueprint("ttl", __name__)

    def _get_ttl():
        try:
            return int(request.args.get("ttl", DEFAULT_TTL))
        except (ValueError, TypeError):
            return DEFAULT_TTL

    @bp.route("/ttl/summary", methods=["GET"])
    def summary():
        """Return TTL summary for all stored requests."""
        ttl = _get_ttl()
        return jsonify(ttl_summary(store, ttl))

    @bp.route("/ttl/expire", methods=["DELETE"])
    def expire():
        """Expire (remove) all requests older than ttl seconds."""
        ttl = _get_ttl()
        removed = expire_requests(store, ttl)
        return jsonify({"removed": len(removed), "ids": removed})

    @bp.route("/ttl/check/<request_id>", methods=["GET"])
    def check(request_id):
        """Check TTL status for a specific request."""
        ttl = _get_ttl()
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        remaining = seconds_until_expiry(req, ttl)
        return jsonify({
            "id": request_id,
            "ttl_seconds": ttl,
            "seconds_remaining": round(remaining, 2),
            "expired": remaining <= 0,
        })

    app.register_blueprint(bp)
