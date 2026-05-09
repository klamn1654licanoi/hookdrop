from flask import Blueprint, jsonify, request as flask_request
from hookdrop.scoring import sort_by_score


def init_scoring_sort_routes(app, store):
    bp = Blueprint("scoring_sort", __name__)

    @bp.route("/requests/sorted-by-score", methods=["GET"])
    def sorted_by_score():
        """Return all requests sorted by their score.

        Query params:
          order: 'asc' or 'desc' (default: 'desc')
        """
        order = flask_request.args.get("order", "desc").lower()
        if order not in ("asc", "desc"):
            return jsonify({"error": "order must be 'asc' or 'desc'"}), 400
        descending = order == "desc"
        results = sort_by_score(store, descending=descending)
        return jsonify([r.to_dict() for r in results])

    app.register_blueprint(bp)
