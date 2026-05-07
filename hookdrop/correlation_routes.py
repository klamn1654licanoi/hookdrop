from flask import Blueprint, jsonify, request
from hookdrop.correlation import (
    set_correlation,
    get_correlation,
    remove_correlation,
    get_correlated_requests,
    list_all_correlations,
)


def init_correlation_routes(app, store):
    bp = Blueprint("correlation", __name__)

    @bp.route("/requests/<req_id>/correlation", methods=["GET"])
    def get_correlation_route(req_id):
        if store.get(req_id) is None:
            return jsonify({"error": "not found"}), 404
        correlation_id = get_correlation(store, req_id)
        return jsonify({"request_id": req_id, "correlation_id": correlation_id})

    @bp.route("/requests/<req_id>/correlation", methods=["PUT"])
    def set_correlation_route(req_id):
        if store.get(req_id) is None:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        correlation_id = data.get("correlation_id")
        if not correlation_id:
            return jsonify({"error": "correlation_id required"}), 400
        set_correlation(store, req_id, correlation_id)
        return jsonify({"request_id": req_id, "correlation_id": correlation_id})

    @bp.route("/requests/<req_id>/correlation", methods=["DELETE"])
    def remove_correlation_route(req_id):
        if store.get(req_id) is None:
            return jsonify({"error": "not found"}), 404
        remove_correlation(store, req_id)
        return jsonify({"request_id": req_id, "correlation_id": None})

    @bp.route("/correlations/<correlation_id>/requests", methods=["GET"])
    def correlated_requests_route(correlation_id):
        requests_list = get_correlated_requests(store, correlation_id)
        return jsonify({
            "correlation_id": correlation_id,
            "requests": [r.id for r in requests_list],
            "count": len(requests_list),
        })

    @bp.route("/correlations", methods=["GET"])
    def list_correlations_route():
        all_corr = list_all_correlations(store)
        return jsonify({"correlations": all_corr})

    app.register_blueprint(bp)
