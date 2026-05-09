"""Flask routes for managing and querying throttle rules."""

from flask import Blueprint, jsonify, request, current_app
from hookdrop import throttle as thr


def init_throttle_routes(app, store):
    bp = Blueprint("throttle", __name__)

    @bp.get("/throttle/rules")
    def list_rules():
        return jsonify(thr.list_throttle_rules())

    @bp.post("/throttle/rules")
    def add_rule():
        data = request.get_json(force=True, silent=True) or {}
        key = data.get("key")
        max_requests = data.get("max_requests")
        window_seconds = data.get("window_seconds")
        if not key or max_requests is None or window_seconds is None:
            return jsonify({"error": "key, max_requests and window_seconds required"}), 400
        try:
            thr.set_throttle_rule(key, int(max_requests), int(window_seconds))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        return jsonify({"key": key, "max_requests": max_requests, "window_seconds": window_seconds}), 201

    @bp.get("/throttle/rules/<path:key>")
    def get_rule(key):
        rule = thr.get_throttle_rule(key)
        if rule is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"key": key, "max_requests": rule[0], "window_seconds": rule[1]})

    @bp.delete("/throttle/rules/<path:key>")
    def delete_rule(key):
        removed = thr.remove_throttle_rule(key)
        if not removed:
            return jsonify({"error": "not found"}), 404
        return jsonify({"deleted": key})

    @bp.delete("/throttle/rules")
    def clear_all():
        thr.clear_throttle_rules()
        return jsonify({"cleared": True})

    @bp.get("/throttle/check/<path:key>")
    def check_throttle(key):
        throttled = thr.is_throttled(store, key)
        return jsonify({"key": key, "throttled": throttled})

    @bp.get("/throttle/summary")
    def summary():
        return jsonify(thr.throttle_summary(store))

    app.register_blueprint(bp)
