from flask import Blueprint, jsonify, request
from hookdrop.storage import RequestStore
import hookdrop.retry as retry_module


def init_retry_routes(app, store: RequestStore):
    bp = Blueprint("retry", __name__)

    @bp.route("/requests/<request_id>/retry/policy", methods=["GET"])
    def get_policy(request_id):
        policy = retry_module.get_retry_policy(request_id)
        if policy is None:
            return jsonify({"error": "No retry policy set"}), 404
        return jsonify(policy)

    @bp.route("/requests/<request_id>/retry/policy", methods=["POST"])
    def set_policy(request_id):
        data = request.get_json(silent=True) or {}
        max_attempts = int(data.get("max_attempts", 3))
        delay_seconds = float(data.get("delay_seconds", 5.0))
        if max_attempts < 1 or max_attempts > 20:
            return jsonify({"error": "max_attempts must be between 1 and 20"}), 400
        ok = retry_module.set_retry_policy(request_id, store, max_attempts, delay_seconds)
        if not ok:
            return jsonify({"error": "Request not found"}), 404
        return jsonify(retry_module.get_retry_policy(request_id)), 201

    @bp.route("/requests/<request_id>/retry/policy", methods=["DELETE"])
    def delete_policy(request_id):
        removed = retry_module.remove_retry_policy(request_id)
        if not removed:
            return jsonify({"error": "No retry policy found"}), 404
        return "", 204

    @bp.route("/requests/<request_id>/retry/history", methods=["GET"])
    def history(request_id):
        return jsonify(retry_module.get_retry_history(request_id))

    @bp.route("/requests/<request_id>/retry/summary", methods=["GET"])
    def summary(request_id):
        return jsonify(retry_module.retry_summary(request_id))

    app.register_blueprint(bp)
