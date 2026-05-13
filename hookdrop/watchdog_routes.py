"""Flask routes for the watchdog feature."""

from flask import Blueprint, Flask, jsonify, request

from hookdrop import watchdog as wd

_bp = Blueprint("watchdog", __name__)


def init_watchdog_routes(app: Flask) -> None:
    app.register_blueprint(_bp)


@_bp.route("/watchdog/rules", methods=["GET"])
def list_rules():
    return jsonify(wd.list_watchdog_rules()), 200


@_bp.route("/watchdog/rules", methods=["POST"])
def add_rule():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name")
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    try:
        rule = wd.add_watchdog_rule(
            name=name,
            method=data.get("method"),
            path_contains=data.get("path_contains"),
            max_per_minute=int(data.get("max_per_minute", 60)),
            min_per_minute=int(data.get("min_per_minute", 0)),
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(rule), 201


@_bp.route("/watchdog/rules/<name>", methods=["GET"])
def get_rule(name):
    rule = wd.get_watchdog_rule(name)
    if rule is None:
        return jsonify({"error": "Rule not found"}), 404
    return jsonify(rule), 200


@_bp.route("/watchdog/rules/<name>", methods=["DELETE"])
def delete_rule(name):
    removed = wd.remove_watchdog_rule(name)
    if not removed:
        return jsonify({"error": "Rule not found"}), 404
    return jsonify({"deleted": name}), 200


@_bp.route("/watchdog/evaluate", methods=["GET"])
def evaluate_all():
    return jsonify(wd.evaluate_all()), 200


@_bp.route("/watchdog/evaluate/<name>", methods=["GET"])
def evaluate_one(name):
    try:
        result = wd.evaluate_rule(name)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(result), 200


@_bp.route("/watchdog/rules", methods=["DELETE"])
def clear_rules():
    wd.clear_watchdog_rules()
    return jsonify({"cleared": True}), 200
