from flask import Blueprint, jsonify, request
from hookdrop.scoring import set_score, get_score, remove_score, list_all_scores, filter_by_min_score


def init_scoring_routes(app, store):
    bp = Blueprint("scoring", __name__)

    @bp.route("/requests/<req_id>/score", methods=["GET"])
    def get_score_route(req_id):
        req = store.get(req_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        score = get_score(store, req_id)
        return jsonify({"id": req_id, "score": score})

    @bp.route("/requests/<req_id>/score", methods=["PUT"])
    def set_score_route(req_id):
        req = store.get(req_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        data = request.get_json(silent=True) or {}
        value = data.get("score")
        if value is None or not isinstance(value, (int, float)):
            return jsonify({"error": "score must be a number"}), 400
        set_score(store, req_id, value)
        return jsonify({"id": req_id, "score": value})

    @bp.route("/requests/<req_id>/score", methods=["DELETE"])
    def delete_score_route(req_id):
        req = store.get(req_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        remove_score(store, req_id)
        return jsonify({"id": req_id, "score": None})

    @bp.route("/scores", methods=["GET"])
    def all_scores():
        scores = list_all_scores(store)
        return jsonify(scores)

    @bp.route("/scores/filter", methods=["GET"])
    def filter_scores():
        try:
            min_score = float(request.args.get("min", 0))
        except ValueError:
            return jsonify({"error": "min must be a number"}), 400
        results = filter_by_min_score(store, min_score)
        return jsonify([r.to_dict() for r in results])

    app.register_blueprint(bp)
