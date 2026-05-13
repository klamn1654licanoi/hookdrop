"""Routes for accessing replay history."""

from flask import Blueprint, jsonify, current_app
from hookdrop import replay_history as rh


def init_replay_history_routes(app, store):
    bp = Blueprint("replay_history", __name__)

    def _get_store():
        return store

    @bp.route("/replay-history", methods=["GET"])
    def all_history():
        """Return all replay history across all requests."""
        return jsonify(rh.list_all_replayed())

    @bp.route("/replay-history/<request_id>", methods=["GET"])
    def request_history(request_id):
        """Return replay history for a specific request."""
        req = _get_store().get(request_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        return jsonify(rh.get_replay_history(request_id))

    @bp.route("/replay-history/<request_id>/summary", methods=["GET"])
    def request_summary(request_id):
        """Return replay summary for a specific request."""
        req = _get_store().get(request_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        return jsonify(rh.replay_summary(request_id))

    @bp.route("/replay-history/<request_id>", methods=["DELETE"])
    def clear_history(request_id):
        """Clear replay history for a specific request."""
        req = _get_store().get(request_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        rh.clear_replay_history(request_id)
        return jsonify({"status": "cleared", "request_id": request_id})

    app.register_blueprint(bp)
