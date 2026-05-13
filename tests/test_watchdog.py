"""Unit tests for hookdrop/watchdog.py"""

import time
import pytest
from hookdrop import watchdog as wd


@pytest.fixture(autouse=True)
def reset():
    wd.clear_watchdog_rules()
    yield
    wd.clear_watchdog_rules()


def test_add_and_list_rule():
    rule = wd.add_watchdog_rule("high-post", method="POST", max_per_minute=10)
    assert rule["name"] == "high-post"
    assert rule["method"] == "POST"
    assert rule["max_per_minute"] == 10
    assert len(wd.list_watchdog_rules()) == 1


def test_add_rule_method_uppercased():
    rule = wd.add_watchdog_rule("r", method="get")
    assert rule["method"] == "GET"


def test_add_rule_empty_name_raises():
    with pytest.raises(ValueError, match="name"):
        wd.add_watchdog_rule("")


def test_add_rule_invalid_limits_raises():
    with pytest.raises(ValueError):
        wd.add_watchdog_rule("r", max_per_minute=-1)
    with pytest.raises(ValueError):
        wd.add_watchdog_rule("r", min_per_minute=50, max_per_minute=10)


def test_get_rule_not_found():
    assert wd.get_watchdog_rule("missing") is None


def test_remove_rule_existing():
    wd.add_watchdog_rule("r")
    assert wd.remove_watchdog_rule("r") is True
    assert wd.get_watchdog_rule("r") is None


def test_remove_rule_missing():
    assert wd.remove_watchdog_rule("ghost") is False


def test_evaluate_rule_no_hits():
    wd.add_watchdog_rule("quiet", max_per_minute=5, min_per_minute=0)
    result = wd.evaluate_rule("quiet")
    assert result["hits_last_minute"] == 0
    assert result["breached"] is False


def test_evaluate_rule_exceeds_max():
    wd.add_watchdog_rule("busy", max_per_minute=2)
    for _ in range(5):
        wd.record_hit("busy")
    result = wd.evaluate_rule("busy")
    assert result["hits_last_minute"] == 5
    assert result["breached"] is True


def test_evaluate_rule_below_min():
    wd.add_watchdog_rule("expected", min_per_minute=5, max_per_minute=100)
    wd.record_hit("expected")
    result = wd.evaluate_rule("expected")
    assert result["breached"] is True


def test_evaluate_rule_not_found_raises():
    with pytest.raises(KeyError):
        wd.evaluate_rule("nonexistent")


def test_evaluate_all_returns_all():
    wd.add_watchdog_rule("a")
    wd.add_watchdog_rule("b")
    results = wd.evaluate_all()
    names = {r["name"] for r in results}
    assert names == {"a", "b"}


def test_old_hits_excluded_from_window(monkeypatch):
    wd.add_watchdog_rule("timed", max_per_minute=2)
    # Manually inject an old hit
    wd._watchdog_hits["timed"] = [time.time() - 120, time.time()]
    result = wd.evaluate_rule("timed")
    assert result["hits_last_minute"] == 1
