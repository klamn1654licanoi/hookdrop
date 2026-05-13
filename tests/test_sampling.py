"""Tests for hookdrop.sampling."""

import pytest
from hookdrop.storage import RequestStore, WebhookRequest
from hookdrop import sampling
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def reset_rate():
    sampling.reset_sampling_rate()
    yield
    sampling.reset_sampling_rate()


@pytest.fixture
def store():
    return RequestStore()


def _make_request(store: RequestStore, path: str = "/hook") -> WebhookRequest:
    req = WebhookRequest(
        id=f"req-{path.strip('/')}-{id(object())}",
        method="POST",
        path=path,
        headers={"content-type": "application/json"},
        body='{"x": 1}',
        timestamp=datetime.now(timezone.utc).isoformat(),
        status_code=200,
    )
    store.save(req)
    return req


def test_default_sampling_rate_is_one():
    assert sampling.get_sampling_rate() == 1.0


def test_set_sampling_rate_valid():
    sampling.set_sampling_rate(0.5)
    assert sampling.get_sampling_rate() == 0.5


def test_set_sampling_rate_zero():
    sampling.set_sampling_rate(0.0)
    assert sampling.get_sampling_rate() == 0.0


def test_set_sampling_rate_one():
    sampling.set_sampling_rate(1.0)
    assert sampling.get_sampling_rate() == 1.0


def test_set_sampling_rate_invalid_high():
    with pytest.raises(ValueError):
        sampling.set_sampling_rate(1.5)


def test_set_sampling_rate_invalid_low():
    with pytest.raises(ValueError):
        sampling.set_sampling_rate(-0.1)


def test_reset_sampling_rate():
    sampling.set_sampling_rate(0.3)
    sampling.reset_sampling_rate()
    assert sampling.get_sampling_rate() == 1.0


def test_should_sample_always_at_rate_one():
    sampling.set_sampling_rate(1.0)
    results = [sampling.should_sample() for _ in range(100)]
    assert all(results)


def test_should_sample_never_at_rate_zero():
    sampling.set_sampling_rate(0.0)
    results = [sampling.should_sample() for _ in range(100)]
    assert not any(results)


def test_sample_requests_rate_one(store):
    for i in range(5):
        _make_request(store, f"/hook/{i}")
    result = sampling.sample_requests(store, rate=1.0)
    assert len(result) == 5


def test_sample_requests_rate_zero(store):
    for i in range(5):
        _make_request(store, f"/hook/{i}")
    result = sampling.sample_requests(store, rate=0.0)
    assert len(result) == 0


def test_sample_requests_empty_store(store):
    result = sampling.sample_requests(store, rate=0.5)
    assert result == []


def test_sample_requests_invalid_rate(store):
    with pytest.raises(ValueError):
        sampling.sample_requests(store, rate=2.0)


def test_sampling_summary(store):
    sampling.set_sampling_rate(0.5)
    for i in range(4):
        _make_request(store, f"/hook/{i}")
    summary = sampling.sampling_summary(store)
    assert summary["sampling_rate"] == 0.5
    assert summary["sampling_percent"] == 50.0
    assert summary["total_requests"] == 4
    assert summary["expected_sampled"] == 2


def test_sampling_summary_uses_global_rate(store):
    sampling.set_sampling_rate(0.25)
    summary = sampling.sampling_summary(store)
    assert summary["sampling_rate"] == 0.25
    assert summary["sampling_percent"] == 25.0
