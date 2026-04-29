"""Flask routes for exporting stored webhook requests."""

from flask import Blueprint, jsonify, request, Response
from hookdrop.storage import RequestStore
from hookdrop import export


def init_export_routes(app, store: RequestStore):
    bp = Blueprint("export", __name__)

    @bp.route("/export/json", methods=["GET"])
    def export_json():
        """Export all stored requests as a JSON array."""
        requests_list = store.all()
        return Response(
            export.to_json(requests_list),
            status=200,
            mimetype="application/json",
        )

    @bp.route("/export/curl", methods=["GET"])
    def export_curl():
        """Export all stored requests as curl commands."""
        target_url = request.args.get("target")
        requests_list = store.all()
        curl_output = export.to_curl_all(requests_list, target_url=target_url)
        return Response(curl_output, status=200, mimetype="text/plain")

    @bp.route("/export/curl/<request_id>", methods=["GET"])
    def export_curl_single(request_id):
        """Export a single request as a curl command."""
        target_url = request.args.get("target")
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "Request not found"}), 404
        curl_cmd = export.to_curl(req, target_url=target_url)
        return Response(curl_cmd, status=200, mimetype="text/plain")

    app.register_blueprint(bp)
