import time
import pytest
from hookdrop import circuit_breaker as cb


@pytest.fixture(autouse=True)
def reset_all():
    cb.reset_all()
    yield
    cb.reset_all()


def test_initial_state_is_closed():
    state = cb.get_state("http://example.com")
    assert state["state"] == cb.CLOSED
    assert state["failure_count"] == 0
    assert state["success_count"] == 0


def test_record_success_increments_count():
    cb.record_success("http://example.com")
    state = cb.get_state("http://example.com")
    assert state["success_count"] == 1
    assert state["state"] == cb.CLOSED


def test_record_failure_increments_count():
    cb.record_failure("http://example.com")
    state = cb.get_state("http://example.com")
    assert state["failure_count"] == 1
    assert state["state"] == cb.CLOSED


def test_circuit_opens_after_threshold():
    target = "http://example.com"
    for _ in range(5):
        cb.record_failure(target)
    state = cb.get_state(target)
    assert state["state"] == cb.OPEN


def test_is_open_returns_true_when_open():
    target = "http://example.com"
    for _ in range(5):
        cb.record_failure(target)
    assert cb.is_open(target) is True


def test_is_open_returns_false_when_closed():
    assert cb.is_open("http://example.com") is False


def test_circuit_transitions_to_half_open_after_timeout():
    target = "http://example.com"
    cb.configure(target, threshold=2, recovery_timeout=0.05)
    cb.record_failure(target)
    cb.record_failure(target)
    assert cb.get_state(target)["state"] == cb.OPEN
    time.sleep(0.1)
    # is_open triggers the half-open transition
    result = cb.is_open(target)
    assert result is False
    assert cb.get_state(target)["state"] == cb.HALF_OPEN


def test_success_in_half_open_closes_circuit():
    target = "http://example.com"
    cb.configure(target, threshold=1, recovery_timeout=0.05)
    cb.record_failure(target)
    time.sleep(0.1)
    cb.is_open(target)  # triggers half-open
    cb.record_success(target)
    assert cb.get_state(target)["state"] == cb.CLOSED


def test_configure_updates_threshold():
    target = "http://example.com"
    cb.configure(target, threshold=10, recovery_timeout=120.0)
    state = cb.get_state(target)
    assert state["threshold"] == 10
    assert state["recovery_timeout"] == 120.0


def test_configure_invalid_threshold_raises():
    with pytest.raises(ValueError, match="threshold"):
        cb.configure("http://example.com", threshold=0)


def test_configure_invalid_timeout_raises():
    with pytest.raises(ValueError, match="recovery_timeout"):
        cb.configure("http://example.com", recovery_timeout=-1)


def test_reset_removes_circuit():
    cb.record_failure("http://example.com")
    cb.reset("http://example.com")
    state = cb.get_state("http://example.com")
    assert state["failure_count"] == 0


def test_list_all_returns_all_targets():
    cb.record_failure("http://a.com")
    cb.record_failure("http://b.com")
    all_states = cb.list_all()
    targets = [s["target"] for s in all_states]
    assert "http://a.com" in targets
    assert "http://b.com" in targets


def test_circuit_does_not_open_before_threshold():
    target = "http://example.com"
    cb.configure(target, threshold=3)
    cb.record_failure(target)
    cb.record_failure(target)
    assert cb.get_state(target)["state"] == cb.CLOSED
    assert cb.is_open(target) is False
