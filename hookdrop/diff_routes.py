"""Routes for request diffing."""

from flask import Blueprint, jsonify
from hookdrop.storage import RequestStore
from hookdrop.diff import diff_requests


def init_diff_routes(app, store: RequestStore):
    bp = Blueprint("diff", __name__)

    @bp.route("/diff/<id_a>/<id_b>", methods=["GET"])
    def compare(id_a: str, id_b: str):
        """Compare two requests by their IDs."""
        req_a = store.get(id_a)
        req_b = store.get(id_b)

        if req_a is None:
            return jsonify({"error": f"Request '{id_a}' not found"}), 404
        if req_b is None:
            return jsonify({"error": f"Request '{id_b}' not found"}), 404

        result = diff_requests(req_a, req_b)
        return jsonify(result), 200

    app.register_blueprint(bp)
