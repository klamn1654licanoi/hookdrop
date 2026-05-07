"""Request pipeline: define ordered processing steps applied to incoming webhooks."""

from typing import Dict, List, Optional

_pipelines: Dict[str, List[Dict]] = {}

STEP_TYPES = {"filter", "transform", "tag", "label", "priority", "route"}


def create_pipeline(name: str) -> Dict:
    if name in _pipelines:
        raise ValueError(f"Pipeline '{name}' already exists")
    _pipelines[name] = []
    return {"name": name, "steps": []}


def delete_pipeline(name: str) -> bool:
    if name not in _pipelines:
        return False
    del _pipelines[name]
    return True


def get_pipeline(name: str) -> Optional[Dict]:
    if name not in _pipelines:
        return None
    return {"name": name, "steps": list(_pipelines[name])}


def list_pipelines() -> List[Dict]:
    return [{"name": name, "steps": list(steps)} for name, steps in _pipelines.items()]


def add_step(name: str, step_type: str, config: Dict) -> Dict:
    if name not in _pipelines:
        raise KeyError(f"Pipeline '{name}' not found")
    if step_type not in STEP_TYPES:
        raise ValueError(f"Invalid step type '{step_type}'. Must be one of {STEP_TYPES}")
    step = {"type": step_type, "config": config}
    _pipelines[name].append(step)
    return step


def remove_step(name: str, index: int) -> bool:
    if name not in _pipelines:
        raise KeyError(f"Pipeline '{name}' not found")
    steps = _pipelines[name]
    if index < 0 or index >= len(steps):
        return False
    steps.pop(index)
    return True


def clear_steps(name: str) -> bool:
    if name not in _pipelines:
        return False
    _pipelines[name] = []
    return True


def clear_all() -> None:
    _pipelines.clear()
