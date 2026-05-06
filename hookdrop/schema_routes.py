"""Routes for managing and testing webhook schema validation."""

from flask import Blueprint, request, jsonify
from hookdrop import schema as schema_module


def init_schema_routes(app, store):
    bp = Blueprint("schema", __name__)

    @bp.route("/schemas", methods=["GET"])
    def list_schemas():
        return jsonify(schema_module.list_schemas())

    @bp.route("/schemas/<path:pattern>", methods=["GET"])
    def get_schema(pattern):
        s = schema_module.get_schema(pattern)
        if s is None:
            return jsonify({"error": "Schema not found"}), 404
        return jsonify({"pattern": pattern, "schema": s})

    @bp.route("/schemas/<path:pattern>", methods=["PUT"])
    def register_schema(pattern):
        data = request.get_json(silent=True)
        if not data or "schema" not in data:
            return jsonify({"error": "Request body must include 'schema'"}), 400
        schema_module.register_schema(pattern, data["schema"])
        return jsonify({"registered": pattern}), 201

    @bp.route("/schemas/<path:pattern>", methods=["DELETE"])
    def delete_schema(pattern):
        removed = schema_module.unregister_schema(pattern)
        if not removed:
            return jsonify({"error": "Schema not found"}), 404
        return jsonify({"deleted": pattern})

    @bp.route("/schemas/validate/<req_id>", methods=["GET"])
    def validate_request(req_id):
        req = store.get(req_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        valid, errors = schema_module.validate_request(req.path, req.body)
        return jsonify({
            "id": req_id,
            "valid": valid,
            "errors": errors,
        })

    app.register_blueprint(bp)
