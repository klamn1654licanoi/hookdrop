"""Flask routes for pipeline management."""

from flask import Blueprint, jsonify, request
from hookdrop import pipeline as pl


def init_pipeline_routes(app):
    bp = Blueprint("pipeline", __name__)

    @bp.route("/pipelines", methods=["GET"])
    def list_pipelines():
        return jsonify(pl.list_pipelines()), 200

    @bp.route("/pipelines", methods=["POST"])
    def create_pipeline():
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name", "").strip()
        if not name:
            return jsonify({"error": "'name' is required"}), 400
        try:
            result = pl.create_pipeline(name)
        except ValueError as e:
            return jsonify({"error": str(e)}), 409
        return jsonify(result), 201

    @bp.route("/pipelines/<name>", methods=["GET"])
    def get_pipeline(name):
        p = pl.get_pipeline(name)
        if p is None:
            return jsonify({"error": "Pipeline not found"}), 404
        return jsonify(p), 200

    @bp.route("/pipelines/<name>", methods=["DELETE"])
    def delete_pipeline(name):
        if not pl.delete_pipeline(name):
            return jsonify({"error": "Pipeline not found"}), 404
        return "", 204

    @bp.route("/pipelines/<name>/steps", methods=["POST"])
    def add_step(name):
        data = request.get_json(force=True, silent=True) or {}
        step_type = data.get("type", "")
        config = data.get("config", {})
        try:
            step = pl.add_step(name, step_type, config)
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        return jsonify(step), 201

    @bp.route("/pipelines/<name>/steps/<int:index>", methods=["DELETE"])
    def remove_step(name, index):
        try:
            removed = pl.remove_step(name, index)
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        if not removed:
            return jsonify({"error": "Step index out of range"}), 404
        return "", 204

    @bp.route("/pipelines/<name>/steps", methods=["DELETE"])
    def clear_steps(name):
        if not pl.clear_steps(name):
            return jsonify({"error": "Pipeline not found"}), 404
        return "", 204

    app.register_blueprint(bp)
