"""Flask routes for tag management."""

from flask import Blueprint, jsonify, request, current_app
from hookdrop.tags import add_tag, remove_tag, get_tags, filter_by_tag, list_all_tags
from hookdrop.storage import to_dict

tag_bp = Blueprint("tags", __name__)


def init_tag_routes(app, store):
    app.config["STORE"] = store
    app.register_blueprint(tag_bp)


@tag_bp.route("/requests/<request_id>/tags", methods=["GET"])
def list_tags(request_id):
    store = current_app.config["STORE"]
    tags = get_tags(store, request_id)
    if tags is None:
        return jsonify({"error": "Request not found"}), 404
    return jsonify({"id": request_id, "tags": tags})


@tag_bp.route("/requests/<request_id>/tags", methods=["POST"])
def add_tag_route(request_id):
    store = current_app.config["STORE"]
    data = request.get_json(silent=True) or {}
    tag = data.get("tag", "").strip()
    if not tag:
        return jsonify({"error": "'tag' field is required"}), 400
    success = add_tag(store, request_id, tag)
    if not success:
        return jsonify({"error": "Request not found"}), 404
    return jsonify({"id": request_id, "tags": get_tags(store, request_id)})


@tag_bp.route("/requests/<request_id>/tags/<tag>", methods=["DELETE"])
def remove_tag_route(request_id, tag):
    store = current_app.config["STORE"]
    success = remove_tag(store, request_id, tag)
    if not success:
        return jsonify({"error": "Request not found"}), 404
    return jsonify({"id": request_id, "tags": get_tags(store, request_id)})


@tag_bp.route("/tags", methods=["GET"])
def all_tags():
    store = current_app.config["STORE"]
    return jsonify({"tags": list_all_tags(store)})


@tag_bp.route("/tags/<tag>/requests", methods=["GET"])
def requests_by_tag(tag):
    store = current_app.config["STORE"]
    results = filter_by_tag(store, tag)
    return jsonify([to_dict(r) for r in results])
