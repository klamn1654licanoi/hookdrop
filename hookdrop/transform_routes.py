"""Flask routes for request transformation endpoints."""

from flask import Blueprint, jsonify, request, current_app
from hookdrop import transform


def init_transform_routes(app, store):
    bp = Blueprint("transform", __name__)

    @bp.route("/requests/<request_id>/transform", methods=["GET"])
    def get_transform(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(transform.get_transforms(req))

    @bp.route("/requests/<request_id>/transform", methods=["DELETE"])
    def clear_transforms(request_id):
        """Remove all transforms applied to the given request."""
        req = transform.clear_transforms(store, request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(transform.get_transforms(req))

    @bp.route("/requests/<request_id>/transform/header", methods=["PUT"])
    def set_header(request_id):
        data = request.get_json(force=True, silent=True) or {}
        key = data.get("key")
        value = data.get("value")
        if not key or value is None:
            return jsonify({"error": "'key' and 'value' are required"}), 400
        req = transform.set_header(store, request_id, key, value)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(transform.get_transforms(req))

    @bp.route("/requests/<request_id>/transform/header", methods=["DELETE"])
    def remove_header(request_id):
        data = request.get_json(force=True, silent=True) or {}
        key = data.get("key")
        if not key:
            return jsonify({"error": "'key' is required"}), 400
        req = transform.remove_header(store, request_id, key)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(transform.get_transforms(req))

    @bp.route("/requests/<request_id>/transform/body", methods=["PUT"])
    def rewrite_body(request_id):
        data = request.get_json(force=True, silent=True) or {}
        new_body = data.get("body", "")
        req = transform.rewrite_body(store, request_id, new_body)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(transform.get_transforms(req))

    @bp.route("/requests/<request_id>/transform/path", methods=["PUT"])
    def rewrite_path(request_id):
        data = request.get_json(force=True, silent=True) or {}
        new_path = data.get("path")
        if not new_path:
            return jsonify({"error": "'path' is required"}), 400
        req = transform.rewrite_path(store, request_id, new_path)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(transform.get_transforms(req))

    app.register_blueprint(bp)
