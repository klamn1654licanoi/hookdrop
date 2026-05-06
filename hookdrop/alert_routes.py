from flask import Blueprint, request, jsonify
from hookdrop import alerts
from hookdrop.storage import RequestStore


def init_alert_routes(app, store: RequestStore):
    bp = Blueprint("alerts", __name__)

    @bp.route("/alerts", methods=["GET"])
    def list_alert_rules():
        return jsonify(alerts.list_alerts())

    @bp.route("/alerts", methods=["POST"])
    def add_alert():
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name")
        condition = data.get("condition")
        value = data.get("value")
        if not name or not condition or value is None:
            return jsonify({"error": "name, condition, and value are required"}), 400
        rule = alerts.add_alert(
            name=name,
            condition=condition,
            value=str(value),
            notify=data.get("notify"),
        )
        return jsonify(rule), 201

    @bp.route("/alerts/<name>", methods=["GET"])
    def get_alert(name):
        rule = alerts.get_alert(name)
        if rule is None:
            return jsonify({"error": "not found"}), 404
        return jsonify(rule)

    @bp.route("/alerts/<name>", methods=["DELETE"])
    def delete_alert(name):
        removed = alerts.remove_alert(name)
        if not removed:
            return jsonify({"error": "not found"}), 404
        return jsonify({"deleted": name})

    @bp.route("/alerts/scan", methods=["GET"])
    def scan():
        results = alerts.scan_store(store)
        return jsonify(results)

    @bp.route("/alerts/evaluate/<request_id>", methods=["GET"])
    def evaluate(request_id):
        req = store.get(request_id)
        if req is None:
            return jsonify({"error": "request not found"}), 404
        triggered = alerts.evaluate_alerts(req)
        return jsonify({"request_id": request_id, "triggered": triggered})

    app.register_blueprint(bp)
