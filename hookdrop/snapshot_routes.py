"""Flask routes for snapshot management."""

from flask import Blueprint, jsonify, request as flask_request
from hookdrop.storage import RequestStore
import hookdrop.snapshots as snapshots


def init_snapshot_routes(app, store: RequestStore):
    bp = Blueprint("snapshots", __name__)

    @bp.route("/snapshots", methods=["GET"])
    def list_all():
        names = snapshots.list_snapshots()
        return jsonify({"snapshots": names})

    @bp.route("/snapshots/<name>", methods=["POST"])
    def save(name):
        count = snapshots.save_snapshot(store, name)
        return jsonify({"snapshot": name, "saved": count}), 201

    @bp.route("/snapshots/<name>/restore", methods=["POST"])
    def restore(name):
        count = snapshots.load_snapshot(store, name)
        if count is None:
            return jsonify({"error": f"Snapshot '{name}' not found"}), 404
        return jsonify({"snapshot": name, "restored": count})

    @bp.route("/snapshots/<name>", methods=["GET"])
    def get(name):
        data = snapshots.get_snapshot(name)
        if data is None:
            return jsonify({"error": f"Snapshot '{name}' not found"}), 404
        return jsonify({"snapshot": name, "requests": data, "count": len(data)})

    @bp.route("/snapshots/<name>", methods=["DELETE"])
    def delete(name):
        deleted = snapshots.delete_snapshot(name)
        if not deleted:
            return jsonify({"error": f"Snapshot '{name}' not found"}), 404
        return jsonify({"deleted": name})

    app.register_blueprint(bp)
