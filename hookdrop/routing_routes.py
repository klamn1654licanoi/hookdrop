"""Flask routes for managing and triggering routing rules."""

from flask import Blueprint, request, jsonify
from hookdrop import routing


def init_routing_routes(app, store):
    bp = Blueprint("routing", __name__)

    @bp.route("/routing/rules", methods=["GET"])
    def list_rules():
        return jsonify(routing.list_rules())

    @bp.route("/routing/rules", methods=["POST"])
    def add_rule():
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name")
        target_url = data.get("target_url")
        if not name or not target_url:
            return jsonify({"error": "name and target_url are required"}), 400
        if routing.get_rule(name):
            return jsonify({"error": f"rule '{name}' already exists"}), 409
        rule = routing.add_rule(name, target_url, data.get("filters", {}))
        return jsonify(rule), 201

    @bp.route("/routing/rules/<name>", methods=["GET"])
    def get_rule(name):
        rule = routing.get_rule(name)
        if rule is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(rule)

    @bp.route("/routing/rules/<name>", methods=["DELETE"])
    def delete_rule(name):
        removed = routing.remove_rule(name)
        if not removed:
            return jsonify({"error": "not found"}), 404
        return jsonify({"deleted": name})

    @bp.route("/routing/rules/<name>/enable", methods=["POST"])
    def enable_rule(name):
        ok = routing.enable_rule(name)
        if not ok:
            return jsonify({"error": "not found"}), 404
        return jsonify({"name": name, "enabled": True})

    @bp.route("/routing/rules/<name>/disable", methods=["POST"])
    def disable_rule(name):
        ok = routing.disable_rule(name)
        if not ok:
            return jsonify({"error": "not found"}), 404
        return jsonify({"name": name, "enabled": False})

    @bp.route("/routing/dispatch/<request_id>", methods=["POST"])
    def dispatch(request_id):
        results = routing.apply_rules(store, request_id)
        if results == [] and store.get(request_id) is None:
            return jsonify({"error": "request not found"}), 404
        return jsonify({"dispatched": results})

    app.register_blueprint(bp)
