"""Flask routes for webhook request grouping."""

from flask import Blueprint, jsonify, request, current_app
from hookdrop import webhook_groups as wg


def init_group_routes(app, store):
    bp = Blueprint("groups", __name__)

    @bp.get("/groups")
    def list_groups():
        return jsonify(wg.list_groups())

    @bp.post("/groups/<name>")
    def create_group(name):
        result = wg.create_group(name)
        status = 201 if result["created"] else 200
        return jsonify(result), status

    @bp.delete("/groups/<name>")
    def delete_group(name):
        deleted = wg.delete_group(name)
        if not deleted:
            return jsonify({"error": "Group not found"}), 404
        return jsonify({"deleted": name})

    @bp.get("/groups/<name>")
    def get_group(name):
        requests = wg.get_group(store, name)
        if requests is None:
            return jsonify({"error": "Group not found"}), 404
        return jsonify({"name": name, "requests": requests})

    @bp.post("/groups/<name>/add/<request_id>")
    def add_to_group(name, request_id):
        ok = wg.add_to_group(store, name, request_id)
        if not ok:
            return jsonify({"error": "Group or request not found"}), 404
        return jsonify({"group": name, "added": request_id})

    @bp.delete("/groups/<name>/remove/<request_id>")
    def remove_from_group(name, request_id):
        ok = wg.remove_from_group(name, request_id)
        if not ok:
            return jsonify({"error": "Group not found"}), 404
        return jsonify({"group": name, "removed": request_id})

    app.register_blueprint(bp)
