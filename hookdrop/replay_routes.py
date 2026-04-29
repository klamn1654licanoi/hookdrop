from flask import Blueprint, jsonify, request
from hookdrop.storage import RequestStore
from hookdrop.replay import build_replay_request, replay_request

replay_bp = Blueprint("replay", __name__)
_store: RequestStore = None


def init_replay_routes(app, store: RequestStore):
    global _store
    _store = store
    app.register_blueprint(replay_bp)


@replay_bp.route("/requests/<request_id>/replay", methods=["POST"])
def replay(request_id: str):
    """Replay a previously received webhook request to a target URL."""
    req = _store.get(request_id)
    if req is None:
        return jsonify({"error": f"Request '{request_id}' not found"}), 404

    body = request.get_json(silent=True) or {}
    target_url = body.get("target_url")
    if not target_url:
        return jsonify({"error": "'target_url' is required in the request body"}), 400

    timeout = body.get("timeout", 10)

    try:
        prepared = build_replay_request(req, target_url)
        response = replay_request(prepared, timeout=timeout)
        return jsonify({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text,
            "url": response.url,
        }), 200
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502
