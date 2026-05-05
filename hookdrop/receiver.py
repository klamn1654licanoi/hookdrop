"""Main Flask application factory for hookdrop."""

from flask import Flask, request, jsonify
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop.filter_routes import init_filter_routes
from hookdrop.export_routes import init_export_routes
from hookdrop.replay_routes import init_replay_routes
from hookdrop.stats_routes import init_stats_routes
from hookdrop.tag_routes import init_tag_routes
from hookdrop.notes_routes import init_notes_routes
from hookdrop.bookmark_routes import init_bookmark_routes
from hookdrop.diff_routes import init_diff_routes
from hookdrop.snapshot_routes import init_snapshot_routes


def create_app(store: RequestStore = None) -> Flask:
    if store is None:
        store = RequestStore()

    app = Flask(__name__)

    @app.route("/webhook", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    @app.route("/webhook/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    def receive(path):
        req = WebhookRequest(
            method=request.method,
            path="/" + path if path else "/",
            headers=dict(request.headers),
            body=request.get_data(as_text=True),
        )
        store.save(req)
        return jsonify({"id": req.id, "status": "received"}), 200

    @app.route("/requests", methods=["GET"])
    def list_requests():
        return jsonify([r.to_dict() for r in store.all()])

    @app.route("/requests/<req_id>", methods=["GET"])
    def get_request(req_id):
        req = store.get(req_id)
        if req is None:
            return jsonify({"error": "Not found"}), 404
        return jsonify(req.to_dict())

    @app.route("/requests", methods=["DELETE"])
    def clear_requests():
        store.clear()
        return jsonify({"status": "cleared"})

    init_filter_routes(app, store)
    init_export_routes(app, store)
    init_replay_routes(app, store)
    init_stats_routes(app, store)
    init_tag_routes(app, store)
    init_notes_routes(app, store)
    init_bookmark_routes(app, store)
    init_diff_routes(app, store)
    init_snapshot_routes(app, store)

    return app
