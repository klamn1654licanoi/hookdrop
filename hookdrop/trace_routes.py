"""Flask routes for request tracing."""

from flask import Blueprint, jsonify, request, current_app

import hookdrop.trace as trace_module


def init_trace_routes(app, store):
    bp = Blueprint("trace", __name__)

    @bp.route("/traces", methods=["GET"])
    def list_traces():
        return jsonify(trace_module.list_traces())

    @bp.route("/traces", methods=["POST"])
    def create_trace():
        data = request.get_json(silent=True) or {}
        trace_id = data.get("trace_id")
        tid = trace_module.start_trace(trace_id)
        return jsonify({"trace_id": tid}), 201

    @bp.route("/traces/<trace_id>", methods=["GET"])
    def get_trace(trace_id):
        result = trace_module.get_trace(trace_id)
        if result is None:
            return jsonify({"error": "Trace not found"}), 404
        return jsonify({"trace_id": trace_id, "requests": result})

    @bp.route("/traces/<trace_id>", methods=["DELETE"])
    def delete_trace(trace_id):
        deleted = trace_module.delete_trace(trace_id)
        if not deleted:
            return jsonify({"error": "Trace not found"}), 404
        return jsonify({"deleted": trace_id})

    @bp.route("/traces/<trace_id>/attach/<request_id>", methods=["POST"])
    def attach(trace_id, request_id):
        ok = trace_module.attach_trace(store, request_id, trace_id)
        if not ok:
            return jsonify({"error": "Request not found"}), 404
        return jsonify({"trace_id": trace_id, "request_id": request_id})

    @bp.route("/traces/request/<request_id>", methods=["DELETE"])
    def detach(request_id):
        ok = trace_module.detach_trace(request_id)
        if not ok:
            return jsonify({"error": "Request not in any trace"}), 404
        return jsonify({"detached": request_id})

    @bp.route("/traces/request/<request_id>", methods=["GET"])
    def get_trace_for_request(request_id):
        tid = trace_module.get_trace_for_request(request_id)
        if tid is None:
            return jsonify({"trace_id": None})
        return jsonify({"request_id": request_id, "trace_id": tid})

    app.register_blueprint(bp)
