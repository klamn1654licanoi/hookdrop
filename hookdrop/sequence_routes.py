"""Flask routes for request sequence management."""

from flask import Blueprint, request, jsonify, current_app
from hookdrop import sequence as seq_module

_bp = Blueprint("sequence", __name__)


def init_sequence_routes(app):
    app.register_blueprint(_bp, url_prefix="/sequences")


@_bp.route("/", methods=["GET"])
def list_sequences():
    return jsonify(seq_module.list_sequences()), 200


@_bp.route("/", methods=["POST"])
def create_sequence():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    request_ids = data.get("request_ids", [])
    if not name:
        return jsonify({"error": "'name' is required"}), 400
    if not isinstance(request_ids, list) or not request_ids:
        return jsonify({"error": "'request_ids' must be a non-empty list"}), 400
    try:
        result = seq_module.define_sequence(name, request_ids)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result), 201


@_bp.route("/<name>", methods=["GET"])
def get_sequence(name):
    result = seq_module.get_sequence(name)
    if result is None:
        return jsonify({"error": "Sequence not found"}), 404
    return jsonify(result), 200


@_bp.route("/<name>", methods=["DELETE"])
def delete_sequence(name):
    deleted = seq_module.delete_sequence(name)
    if not deleted:
        return jsonify({"error": "Sequence not found"}), 404
    return jsonify({"deleted": name}), 200


@_bp.route("/<name>/validate", methods=["GET"])
def validate_sequence(name):
    store = current_app.config["store"]
    try:
        result = seq_module.validate_sequence(name, store)
    except KeyError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(result), 200
