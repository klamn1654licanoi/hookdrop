"""Flask routes for the request enrichment feature."""

from flask import Blueprint, jsonify, request
from hookdrop import enrichment as enrich_module


def init_enrichment_routes(app, store):
    bp = Blueprint("enrichment", __name__)

    @bp.route("/requests/<request_id>/enrichments", methods=["GET"])
    def get_all(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(enrich_module.get_all_enrichments(request_id))

    @bp.route("/requests/<request_id>/enrichments/<key>", methods=["GET"])
    def get_one(request_id, key):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        value = enrich_module.get_enrichment(request_id, key)
        if value is None:
            return jsonify({"error": "key not found"}), 404
        return jsonify({"key": key, "value": value})

    @bp.route("/requests/<request_id>/enrichments/<key>", methods=["PUT"])
    def set_one(request_id, key):
        body = request.get_json(silent=True) or {}
        if "value" not in body:
            return jsonify({"error": "missing 'value' field"}), 400
        ok = enrich_module.set_enrichment(store, request_id, key, body["value"])
        if not ok:
            return jsonify({"error": "not found"}), 404
        return jsonify({"key": key, "value": body["value"]}), 200

    @bp.route("/requests/<request_id>/enrichments/<key>", methods=["DELETE"])
    def delete_one(request_id, key):
        removed = enrich_module.remove_enrichment(request_id, key)
        if not removed:
            return jsonify({"error": "key not found"}), 404
        return jsonify({"deleted": key})

    @bp.route("/requests/<request_id>/enrichments", methods=["DELETE"])
    def clear_all(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        enrich_module.clear_enrichments(request_id)
        return jsonify({"cleared": request_id})

    @bp.route("/enrichments", methods=["GET"])
    def all_enrichments():
        return jsonify(enrich_module.list_all_enrichments())

    @bp.route("/enrichments/filter", methods=["GET"])
    def filter_by():
        key = request.args.get("key")
        value = request.args.get("value")
        if not key or value is None:
            return jsonify({"error": "'key' and 'value' query params required"}), 400
        matches = enrich_module.filter_by_enrichment(store, key, value)
        return jsonify([r.to_dict() for r in matches])

    app.register_blueprint(bp)
