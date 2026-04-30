"""Flask routes for managing notes on webhook requests."""

from flask import Blueprint, Flask, jsonify, request

from hookdrop import storage
from hookdrop.notes import add_note, get_note, remove_note, requests_with_notes


def init_notes_routes(app: Flask, store: storage.RequestStore) -> None:
    bp = Blueprint("notes", __name__)

    @bp.route("/requests/<request_id>/note", methods=["GET"])
    def get_note_route(request_id: str):
        note = get_note(store, request_id)
        if note is None:
            req = store.get(request_id)
            if req is None:
                return jsonify({"error": "Request not found"}), 404
            return jsonify({"id": request_id, "note": None}), 200
        return jsonify({"id": request_id, "note": note}), 200

    @bp.route("/requests/<request_id>/note", methods=["PUT"])
    def set_note_route(request_id: str):
        body = request.get_json(silent=True) or {}
        note = body.get("note", "")
        if not isinstance(note, str):
            return jsonify({"error": "note must be a string"}), 400
        ok = add_note(store, request_id, note)
        if not ok:
            return jsonify({"error": "Request not found"}), 404
        return jsonify({"id": request_id, "note": note}), 200

    @bp.route("/requests/<request_id>/note", methods=["DELETE"])
    def delete_note_route(request_id: str):
        ok = remove_note(store, request_id)
        if not ok:
            return jsonify({"error": "Request not found"}), 404
        return jsonify({"id": request_id, "note": None}), 200

    @bp.route("/requests/noted", methods=["GET"])
    def list_noted_route():
        noted = requests_with_notes(store)
        return jsonify([r.to_dict() for r in noted]), 200

    app.register_blueprint(bp)
