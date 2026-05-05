from flask import Blueprint, jsonify, request
from hookdrop.storage import RequestStore
import hookdrop.bookmarks as bookmarks_module


def init_bookmark_routes(app, store: RequestStore):
    bp = Blueprint("bookmarks", __name__)

    @bp.route("/bookmarks", methods=["GET"])
    def list_bookmarks():
        return jsonify(bookmarks_module.list_bookmarks())

    @bp.route("/bookmarks/<label>", methods=["PUT"])
    def add_bookmark(label: str):
        data = request.get_json(silent=True) or {}
        request_id = data.get("request_id")
        if not request_id:
            return jsonify({"error": "request_id is required"}), 400
        success = bookmarks_module.add_bookmark(store, request_id, label)
        if not success:
            return jsonify({"error": "request not found"}), 404
        return jsonify({"label": label, "request_id": request_id}), 201

    @bp.route("/bookmarks/<label>", methods=["GET"])
    def get_bookmark(label: str):
        req = bookmarks_module.get_bookmark(store, label)
        if req is None:
            return jsonify({"error": "bookmark not found"}), 404
        from hookdrop.storage import to_dict
        return jsonify(to_dict(req))

    @bp.route("/bookmarks/<label>", methods=["DELETE"])
    def remove_bookmark(label: str):
        success = bookmarks_module.remove_bookmark(label)
        if not success:
            return jsonify({"error": "bookmark not found"}), 404
        return jsonify({"deleted": label})

    app.register_blueprint(bp)
