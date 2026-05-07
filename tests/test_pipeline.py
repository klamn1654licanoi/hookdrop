"""Unit tests for hookdrop.pipeline."""

import pytest
from hookdrop import pipeline as pl


@pytest.fixture(autouse=True)
def reset():
    pl.clear_all()
    yield
    pl.clear_all()


def test_create_pipeline_success():
    result = pl.create_pipeline("my-pipe")
    assert result["name"] == "my-pipe"
    assert result["steps"] == []


def test_create_pipeline_duplicate_raises():
    pl.create_pipeline("dup")
    with pytest.raises(ValueError, match="already exists"):
        pl.create_pipeline("dup")


def test_get_pipeline_not_found():
    assert pl.get_pipeline("missing") is None


def test_list_pipelines_empty():
    assert pl.list_pipelines() == []


def test_list_pipelines_multiple():
    pl.create_pipeline("a")
    pl.create_pipeline("b")
    names = [p["name"] for p in pl.list_pipelines()]
    assert sorted(names) == ["a", "b"]


def test_delete_pipeline_success():
    pl.create_pipeline("del-me")
    assert pl.delete_pipeline("del-me") is True
    assert pl.get_pipeline("del-me") is None


def test_delete_pipeline_not_found():
    assert pl.delete_pipeline("ghost") is False


def test_add_step_success():
    pl.create_pipeline("pipe")
    step = pl.add_step("pipe", "tag", {"value": "important"})
    assert step["type"] == "tag"
    assert step["config"] == {"value": "important"}
    p = pl.get_pipeline("pipe")
    assert len(p["steps"]) == 1


def test_add_step_invalid_type():
    pl.create_pipeline("pipe")
    with pytest.raises(ValueError, match="Invalid step type"):
        pl.add_step("pipe", "unknown", {})


def test_add_step_pipeline_not_found():
    with pytest.raises(KeyError):
        pl.add_step("no-pipe", "tag", {})


def test_remove_step_success():
    pl.create_pipeline("pipe")
    pl.add_step("pipe", "tag", {"value": "x"})
    pl.add_step("pipe", "label", {"key": "env"})
    assert pl.remove_step("pipe", 0) is True
    p = pl.get_pipeline("pipe")
    assert p["steps"][0]["type"] == "label"


def test_remove_step_out_of_range():
    pl.create_pipeline("pipe")
    assert pl.remove_step("pipe", 5) is False


def test_clear_steps():
    pl.create_pipeline("pipe")
    pl.add_step("pipe", "filter", {})
    pl.add_step("pipe", "transform", {})
    assert pl.clear_steps("pipe") is True
    assert pl.get_pipeline("pipe")["steps"] == []


def test_clear_steps_not_found():
    assert pl.clear_steps("nope") is False
