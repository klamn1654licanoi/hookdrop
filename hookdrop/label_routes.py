from flask import Blueprint, jsonify, request as flask_request
from hookdrop.storage import RequestStore
from hookdrop import labels as label_lib


def init_label_routes(app, store: RequestStore):
    bp = Blueprint('labels', __name__)

    @bp.route('/requests/<request_id>/label', methods=['GET'])
    def get_label(request_id):
        label = label_lib.get_label(store, request_id)
        if label_lib.get_label(store, request_id) is None and store.get(request_id) is None:
            return jsonify({'error': 'not found'}), 404
        return jsonify({'id': request_id, 'label': label})

    @bp.route('/requests/<request_id>/label', methods=['PUT'])
    def set_label(request_id):
        data = flask_request.get_json(silent=True) or {}
        label = data.get('label', '').strip()
        if not label:
            return jsonify({'error': 'label is required'}), 400
        ok = label_lib.set_label(store, request_id, label)
        if not ok:
            return jsonify({'error': 'not found'}), 404
        return jsonify({'id': request_id, 'label': label})

    @bp.route('/requests/<request_id>/label', methods=['DELETE'])
    def remove_label(request_id):
        if store.get(request_id) is None:
            return jsonify({'error': 'not found'}), 404
        label_lib.remove_label(store, request_id)
        return jsonify({'id': request_id, 'label': None})

    @bp.route('/labels', methods=['GET'])
    def all_labels():
        counts = label_lib.list_all_labels(store)
        return jsonify({'labels': counts})

    @bp.route('/labels/<label>/requests', methods=['GET'])
    def by_label(label):
        reqs = label_lib.filter_by_label(store, label)
        return jsonify({'label': label, 'requests': [r.to_dict() for r in reqs]})

    app.register_blueprint(bp)
