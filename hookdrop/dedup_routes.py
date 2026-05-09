"""Routes for request deduplication inspection."""

from flask import Blueprint, jsonify, current_app
from hookdrop import dedup


def init_dedup_routes(app, store):
    bp = Blueprint("dedup", __name__)

    @bp.route("/dedup/register/<request_id>", methods=["POST"])
    def register(request_id):
        try:
            fp = dedup.register_request(store, request_id)
            return jsonify({"request_id": request_id, "fingerprint": fp}), 200
        except KeyError as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/dedup/check/<request_id>", methods=["GET"])
    def check(request_id):
        try:
            dup = dedup.is_duplicate(store, request_id)
            dupes = dedup.get_duplicates(store, request_id)
            return jsonify({
                "request_id": request_id,
                "is_duplicate": dup,
                "duplicates": dupes,
            }), 200
        except KeyError as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/dedup/duplicates/<request_id>", methods=["GET"])
    def duplicates(request_id):
        try:
            dupes = dedup.get_duplicates(store, request_id)
            return jsonify({"request_id": request_id, "duplicates": dupes}), 200
        except KeyError as e:
            return jsonify({"error": str(e)}), 404

    @bp.route("/dedup/all", methods=["GET"])
    def all_duplicates():
        groups = dedup.list_all_duplicates()
        return jsonify({"duplicate_groups": groups}), 200

    @bp.route("/dedup/clear", methods=["DELETE"])
    def clear():
        dedup.clear_dedup()
        return jsonify({"status": "cleared"}), 200

    app.register_blueprint(bp)
