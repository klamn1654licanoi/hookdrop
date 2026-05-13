"""Flask routes for request timeout rule management and evaluation."""

from flask import Blueprint, Flask, jsonify, request
from hookdrop import timeouts
from hookdrop.storage import RequestStore


def init_timeout_routes(app: Flask, store: RequestStore) -> None:
    bp = Blueprint("timeouts", __name__, url_prefix="/timeouts")

    @bp.get("/rules")
    def list_rules():
        return jsonify(timeouts.list_timeout_rules())

    @bp.post("/rules")
    def add_rule():
        data = request.get_json(force=True)
        path_prefix = data.get("path_prefix")
        max_seconds = data.get("max_seconds")
        if not path_prefix or max_seconds is None:
            return jsonify({"error": "path_prefix and max_seconds are required"}), 400
        try:
            timeouts.set_timeout_rule(path_prefix, float(max_seconds))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"path_prefix": path_prefix, "max_seconds": max_seconds}), 201

    @bp.get("/rules/<path:prefix>")
    def get_rule(prefix):
        rule = timeouts.get_timeout_rule(prefix)
        if rule is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"path_prefix": prefix, "max_seconds": rule})

    @bp.delete("/rules/<path:prefix>")
    def delete_rule(prefix):
        removed = timeouts.remove_timeout_rule(prefix)
        if not removed:
            return jsonify({"error": "not found"}), 404
        return "", 204

    @bp.post("/evaluate/<request_id>")
    def evaluate(request_id):
        result = timeouts.evaluate_request(store, request_id)
        if result is None:
            return jsonify({"error": "request not found or no rule matched"}), 404
        return jsonify({"id": request_id, "timed_out": result})

    @bp.get("/check/<request_id>")
    def check(request_id):
        result = timeouts.is_timed_out(request_id)
        if result is None:
            return jsonify({"error": "not evaluated yet"}), 404
        return jsonify({"id": request_id, "timed_out": result})

    @bp.get("/flagged")
    def flagged():
        return jsonify(timeouts.list_timed_out(store))

    app.register_blueprint(bp)
