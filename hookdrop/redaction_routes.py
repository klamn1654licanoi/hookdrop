"""Flask routes for managing and previewing redaction rules."""

from flask import Blueprint, Flask, jsonify, request

from hookdrop import redaction
from hookdrop.storage import RequestStore


def init_redaction_routes(app: Flask, store: RequestStore) -> None:
    bp = Blueprint("redaction", __name__)

    @bp.get("/redaction/rules")
    def list_rules():
        return jsonify(redaction.list_rules())

    @bp.post("/redaction/rules")
    def add_rule():
        data = request.get_json(force=True, silent=True) or {}
        field = data.get("field", "").strip()
        if not field:
            return jsonify({"error": "'field' is required"}), 400
        pattern = data.get("pattern", "")
        redaction.add_rule(field, pattern or None)
        return jsonify({"field": field, "pattern": pattern}), 201

    @bp.delete("/redaction/rules/<field>")
    def remove_rule(field: str):
        removed = redaction.remove_rule(field)
        if not removed:
            return jsonify({"error": "rule not found"}), 404
        return jsonify({"removed": field})

    @bp.delete("/redaction/rules")
    def clear_rules():
        redaction.clear_rules()
        return jsonify({"status": "cleared"})

    @bp.get("/redaction/preview/<request_id>")
    def preview(request_id: str):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "request not found"}), 404
        from hookdrop.storage import to_dict
        redacted = redaction.apply_redaction(to_dict(req))
        return jsonify(redacted)

    app.register_blueprint(bp)
