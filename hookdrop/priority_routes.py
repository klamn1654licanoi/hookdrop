from flask import Blueprint, jsonify, request as flask_request
from hookdrop.storage import RequestStore
import hookdrop.priority as priority_module


def init_priority_routes(app, store: RequestStore):
    bp = Blueprint("priority", __name__)

    @bp.route("/requests/<request_id>/priority", methods=["GET"])
    def get_priority(request_id):
        level = priority_module.get_priority(request_id)
        if level is None:
            return jsonify({"priority": None, "request_id": request_id}), 200
        return jsonify({"priority": level, "request_id": request_id}), 200

    @bp.route("/requests/<request_id>/priority", methods=["PUT"])
    def set_priority(request_id):
        data = flask_request.get_json(silent=True) or {}
        level = data.get("priority")
        if not level:
            return jsonify({"error": "Missing 'priority' field"}), 400
        try:
            ok = priority_module.set_priority(store, request_id, level)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        if not ok:
            return jsonify({"error": "Request not found"}), 404
        return jsonify({"request_id": request_id, "priority": level}), 200

    @bp.route("/requests/<request_id>/priority", methods=["DELETE"])
    def remove_priority(request_id):
        removed = priority_module.remove_priority(request_id)
        if not removed:
            return jsonify({"error": "No priority set for this request"}), 404
        return jsonify({"removed": True, "request_id": request_id}), 200

    @bp.route("/requests/priority/<level>", methods=["GET"])
    def by_priority(level):
        try:
            requests = priority_module.filter_by_priority(store, level)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify([r.to_dict() for r in requests]), 200

    @bp.route("/priorities", methods=["GET"])
    def all_priorities():
        mapping = priority_module.list_all_priorities(store)
        return jsonify(mapping), 200

    app.register_blueprint(bp)
