from flask import Blueprint, jsonify
from hookdrop.storage import RequestStore
from hookdrop.stats import compute_stats, most_common_method, most_common_path


def init_stats_routes(app, store: RequestStore):
    bp = Blueprint("stats", __name__)

    @bp.route("/stats", methods=["GET"])
    def stats_summary():
        """Return aggregate statistics for all received webhook requests."""
        data = compute_stats(store)
        return jsonify(data), 200

    @bp.route("/stats/top-method", methods=["GET"])
    def top_method():
        """Return the most commonly used HTTP method."""
        method = most_common_method(store)
        if method is None:
            return jsonify({"method": None, "message": "No requests recorded"}), 200
        return jsonify({"method": method}), 200

    @bp.route("/stats/top-path", methods=["GET"])
    def top_path():
        """Return the most commonly hit request path."""
        path = most_common_path(store)
        if path is None:
            return jsonify({"path": None, "message": "No requests recorded"}), 200
        return jsonify({"path": path}), 200

    app.register_blueprint(bp)
