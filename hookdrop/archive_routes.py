"""Flask routes for archive management."""

from flask import Blueprint, jsonify, current_app
from hookdrop.archive import (
    archive_request,
    unarchive_request,
    is_archived,
    list_archived,
    list_active,
    clear_archived,
)


def init_archive_routes(app, store):
    bp = Blueprint("archive", __name__)

    @bp.route("/archive", methods=["GET"])
    def get_archived():
        """List all archived requests."""
        return jsonify([r.to_dict() for r in list_archived(store)])

    @bp.route("/archive/active", methods=["GET"])
    def get_active():
        """List all non-archived (active) requests."""
        return jsonify([r.to_dict() for r in list_active(store)])

    @bp.route("/archive/<request_id>", methods=["POST"])
    def archive(request_id):
        """Archive a request by ID."""
        if not archive_request(store, request_id):
            return jsonify({"error": "not found"}), 404
        return jsonify({"archived": True, "id": request_id})

    @bp.route("/archive/<request_id>", methods=["DELETE"])
    def unarchive(request_id):
        """Unarchive a request by ID."""
        if not unarchive_request(store, request_id):
            return jsonify({"error": "not found"}), 404
        return jsonify({"archived": False, "id": request_id})

    @bp.route("/archive/<request_id>/status", methods=["GET"])
    def archive_status(request_id):
        """Check if a request is archived."""
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"id": request_id, "archived": is_archived(store, request_id)})

    @bp.route("/archive/clear", methods=["POST"])
    def clear():
        """Delete all archived requests."""
        count = clear_archived(store)
        return jsonify({"cleared": count})

    app.register_blueprint(bp)
