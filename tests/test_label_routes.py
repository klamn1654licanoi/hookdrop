import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.label_routes import init_label_routes


@pytest.fixture
def store():
    s = RequestStore()
    s._store = {}
    s._order = []
    return s


@pytest.fixture
def client(store):
    app = create_app(store)
    init_label_routes(app, store)
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def _post_webhook(client, path='/hook', method='POST'):
    resp = client.open(path, method=method, data='test body',
                       headers={'X-Source': 'test'})
    return resp.get_json()['id']


def test_get_label_not_found(client):
    resp = client.get('/requests/nonexistent/label')
    assert resp.status_code == 404


def test_set_and_get_label(client):
    rid = _post_webhook(client)
    resp = client.put(f'/requests/{rid}/label',
                      json={'label': 'urgent'},
                      content_type='application/json')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['label'] == 'urgent'

    resp2 = client.get(f'/requests/{rid}/label')
    assert resp2.status_code == 200
    assert resp2.get_json()['label'] == 'urgent'


def test_set_label_missing_body(client):
    rid = _post_webhook(client)
    resp = client.put(f'/requests/{rid}/label',
                      json={},
                      content_type='application/json')
    assert resp.status_code == 400


def test_set_label_not_found(client):
    resp = client.put('/requests/ghost/label',
                      json={'label': 'x'},
                      content_type='application/json')
    assert resp.status_code == 404


def test_remove_label(client):
    rid = _post_webhook(client)
    client.put(f'/requests/{rid}/label',
               json={'label': 'debug'},
               content_type='application/json')
    resp = client.delete(f'/requests/{rid}/label')
    assert resp.status_code == 200
    assert resp.get_json()['label'] is None


def test_all_labels_empty(client):
    resp = client.get('/labels')
    assert resp.status_code == 200
    assert resp.get_json()['labels'] == {}


def test_all_labels_with_data(client):
    r1 = _post_webhook(client, path='/a')
    r2 = _post_webhook(client, path='/b')
    client.put(f'/requests/{r1}/label', json={'label': 'error'}, content_type='application/json')
    client.put(f'/requests/{r2}/label', json={'label': 'error'}, content_type='application/json')
    resp = client.get('/labels')
    assert resp.get_json()['labels']['error'] == 2


def test_by_label_route(client):
    rid = _post_webhook(client)
    client.put(f'/requests/{rid}/label', json={'label': 'info'}, content_type='application/json')
    resp = client.get('/labels/info/requests')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['label'] == 'info'
    assert any(r['id'] == rid for r in data['requests'])
