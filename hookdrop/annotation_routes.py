"""Flask routes for the request annotations feature."""

from flask import Blueprint, Flask, jsonify, request
from hookdrop import annotations as ann_module


def init_annotation_routes(app: Flask, store) -> None:
    bp = Blueprint("annotations", __name__)

    @bp.route("/requests/<request_id>/annotations", methods=["GET"])
    def get_all(request_id):
        try:
            data = ann_module.get_all_annotations(store, request_id)
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify(data), 200

    @bp.route("/requests/<request_id>/annotations/<key>", methods=["GET"])
    def get_one(request_id, key):
        try:
            value = ann_module.get_annotation(store, request_id, key)
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        if value is None:
            return jsonify({"error": f"Annotation '{key}' not set"}), 404
        return jsonify({"key": key, "value": value}), 200

    @bp.route("/requests/<request_id>/annotations/<key>", methods=["PUT"])
    def set_one(request_id, key):
        body = request.get_json(silent=True) or {}
        if "value" not in body:
            return jsonify({"error": "'value' is required"}), 400
        try:
            ann_module.set_annotation(store, request_id, key, body["value"])
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        return jsonify({"key": key, "value": body["value"]}), 200

    @bp.route("/requests/<request_id>/annotations/<key>", methods=["DELETE"])
    def delete_one(request_id, key):
        try:
            removed = ann_module.remove_annotation(store, request_id, key)
        except KeyError as e:
            return jsonify({"error": str(e)}), 404
        if not removed:
            return jsonify({"error": f"Annotation '{key}' not found"}), 404
        return jsonify({"removed": key}), 200

    @bp.route("/annotations", methods=["GET"])
    def all_annotations():
        return jsonify(ann_module.list_all_annotations()), 200

    @bp.route("/annotations/filter", methods=["GET"])
    def filter_by():
        key = request.args.get("key")
        value = request.args.get("value")
        if not key or value is None:
            return jsonify({"error": "'key' and 'value' query params required"}), 400
        matches = ann_module.filter_by_annotation(store, key, value)
        return jsonify({"request_ids": matches}), 200

    app.register_blueprint(bp)
