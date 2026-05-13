import pytest
from hookdrop.receiver import create_app
from hookdrop.storage import RequestStore
from hookdrop.masking import clear_mask_rules
from hookdrop.masking_routes import init_masking_routes


@pytest.fixture
def store():
    return RequestStore()


@pytest.fixture
def client(store):
    app = create_app(store)
    init_masking_routes(app, store)
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture(autouse=True)
def clear_rules():
    clear_mask_rules()
    yield
    clear_mask_rules()


def _post_webhook(client, path="/webhook", body=b"secret=abc123", headers=None):
    h = {"Content-Type": "text/plain"}
    if headers:
        h.update(headers)
    res = client.post(path, data=body, headers=h)
    assert res.status_code == 200
    return res.get_json()["id"]


def test_list_rules_empty(client):
    res = client.get("/masking/rules")
    assert res.status_code == 200
    assert res.get_json() == []


def test_add_rule_success(client):
    res = client.post("/masking/rules", json={"field": "Authorization", "pattern": ".*"})
    assert res.status_code == 201
    data = res.get_json()
    assert data["field"] == "Authorization"
    assert data["pattern"] == ".*"
    assert data["mask"] == "***"
    assert "id" in data


def test_add_rule_custom_mask(client):
    res = client.post("/masking/rules", json={"field": "X-Token", "pattern": ".*", "mask": "[REDACTED]"})
    assert res.status_code == 201
    assert res.get_json()["mask"] == "[REDACTED]"


def test_add_rule_missing_field(client):
    res = client.post("/masking/rules", json={"pattern": ".*"})
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_add_rule_missing_pattern(client):
    res = client.post("/masking/rules", json={"field": "Authorization"})
    assert res.status_code == 400


def test_delete_rule(client):
    add_res = client.post("/masking/rules", json={"field": "X-Secret", "pattern": ".*"})
    rule_id = add_res.get_json()["id"]
    del_res = client.delete(f"/masking/rules/{rule_id}")
    assert del_res.status_code == 200
    assert del_res.get_json()["deleted"] == rule_id
    list_res = client.get("/masking/rules")
    assert list_res.get_json() == []


def test_delete_rule_not_found(client):
    res = client.delete("/masking/rules/nonexistent")
    assert res.status_code == 404


def test_clear_all_rules(client):
    client.post("/masking/rules", json={"field": "A", "pattern": "x"})
    client.post("/masking/rules", json={"field": "B", "pattern": "y"})
    res = client.delete("/masking/rules")
    assert res.status_code == 200
    assert res.get_json()["cleared"] is True
    assert client.get("/masking/rules").get_json() == []


def test_preview_not_found(client):
    res = client.get("/masking/preview/does-not-exist")
    assert res.status_code == 404


def test_preview_masks_header(client):
    client.post("/masking/rules", json={"field": "X-Secret", "pattern": ".*"})
    req_id = _post_webhook(client, headers={"X-Secret": "topsecret"})
    res = client.get(f"/masking/preview/{req_id}")
    assert res.status_code == 200
    data = res.get_json()
    assert data["request_id"] == req_id
    assert data["masked_headers"].get("X-Secret") == "***"
