from flask import Blueprint, jsonify, current_app
from hookdrop.pin import pin_request, unpin_request, is_pinned, list_pinned, clear_pins


def init_pin_routes(app, store):
    bp = Blueprint("pins", __name__)

    @bp.route("/pins", methods=["GET"])
    def get_pinned():
        pinned = list_pinned(store)
        return jsonify([r.to_dict() for r in pinned])

    @bp.route("/pins/<request_id>", methods=["GET"])
    def check_pin(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "not found"}), 404
        return jsonify({"id": request_id, "pinned": is_pinned(store, request_id)})

    @bp.route("/pins/<request_id>", methods=["POST"])
    def pin(request_id):
        success = pin_request(store, request_id)
        if not success:
            return jsonify({"error": "not found"}), 404
        return jsonify({"id": request_id, "pinned": True})

    @bp.route("/pins/<request_id>", methods=["DELETE"])
    def unpin(request_id):
        success = unpin_request(store, request_id)
        if not success:
            return jsonify({"error": "not found"}), 404
        return jsonify({"id": request_id, "pinned": False})

    @bp.route("/pins", methods=["DELETE"])
    def clear():
        count = clear_pins(store)
        return jsonify({"cleared": count})

    app.register_blueprint(bp)
