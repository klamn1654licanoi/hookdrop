from flask import Blueprint, jsonify, request
from hookdrop.masking import (
    add_mask_rule,
    remove_mask_rule,
    list_mask_rules,
    clear_mask_rules,
    mask_headers,
    mask_body,
)

masking_bp = Blueprint("masking", __name__)


def init_masking_routes(app, store):
    @masking_bp.route("/masking/rules", methods=["GET"])
    def list_rules():
        return jsonify(list_mask_rules()), 200

    @masking_bp.route("/masking/rules", methods=["POST"])
    def add_rule():
        data = request.get_json(force=True, silent=True) or {}
        field = data.get("field")
        pattern = data.get("pattern")
        mask = data.get("mask", "***")
        if not field or not pattern:
            return jsonify({"error": "'field' and 'pattern' are required"}), 400
        rule = add_mask_rule(field, pattern, mask)
        return jsonify(rule), 201

    @masking_bp.route("/masking/rules/<rule_id>", methods=["DELETE"])
    def delete_rule(rule_id):
        removed = remove_mask_rule(rule_id)
        if not removed:
            return jsonify({"error": "rule not found"}), 404
        return jsonify({"deleted": rule_id}), 200

    @masking_bp.route("/masking/rules", methods=["DELETE"])
    def clear_all_rules():
        clear_mask_rules()
        return jsonify({"cleared": True}), 200

    @masking_bp.route("/masking/preview/<request_id>", methods=["GET"])
    def preview(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "request not found"}), 404
        masked_headers = mask_headers(dict(req.headers))
        masked_body = mask_body(req.body)
        return jsonify({
            "request_id": request_id,
            "masked_headers": masked_headers,
            "masked_body": masked_body,
        }), 200

    app.register_blueprint(masking_bp)
