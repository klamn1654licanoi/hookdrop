"""Flask routes for the request flagging feature."""

from flask import Blueprint, jsonify, request, current_app
from hookdrop import flagging


def init_flagging_routes(app, store):
    bp = Blueprint("flagging", __name__)

    @bp.route("/requests/<request_id>/flags", methods=["GET"])
    def list_flags(request_id):
        if store.get(request_id) is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"flags": flagging.get_flags(request_id)})

    @bp.route("/requests/<request_id>/flags/<flag>", methods=["PUT"])
    def add_flag(request_id, flag):
        try:
            ok = flagging.add_flag(store, request_id, flag)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        if not ok:
            return jsonify({"error": "not found"}), 404
        return jsonify({"flags": flagging.get_flags(request_id)}), 201

    @bp.route("/requests/<request_id>/flags/<flag>", methods=["DELETE"])
    def remove_flag(request_id, flag):
        if store.get(request_id) is None:
            return jsonify({"error": "not found"}), 404
        removed = flagging.remove_flag(store, request_id, flag)
        if not removed:
            return jsonify({"error": "flag not set"}), 404
        return jsonify({"flags": flagging.get_flags(request_id)})

    @bp.route("/flags", methods=["GET"])
    def all_flags():
        return jsonify(flagging.list_all_flags())

    @bp.route("/flags/<flag>/requests", methods=["GET"])
    def by_flag(flag):
        reqs = flagging.filter_by_flag(store, flag)
        return jsonify([r.to_dict() for r in reqs])

    app.register_blueprint(bp)
