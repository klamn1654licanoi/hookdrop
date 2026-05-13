"""Circuit breaker for replay targets — tracks failure rates and opens the circuit
when a target URL exceeds a configurable error threshold."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time

# State constants
CLOSED = "closed"      # normal operation
OPEN = "open"          # blocking requests
HALF_OPEN = "half_open"  # testing recovery

_circuits: Dict[str, dict] = {}


@dataclass
class CircuitState:
    target: str
    state: str = CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    opened_at: Optional[float] = None
    threshold: int = 5
    recovery_timeout: float = 60.0
    history: List[dict] = field(default_factory=list)


def _get_or_create(target: str) -> CircuitState:
    if target not in _circuits:
        _circuits[target] = CircuitState(target=target)
    return _circuits[target]


def record_success(target: str) -> CircuitState:
    cb = _get_or_create(target)
    cb.success_count += 1
    cb.history.append({"result": "success", "time": time.time()})
    if cb.state == HALF_OPEN:
        cb.state = CLOSED
        cb.failure_count = 0
        cb.opened_at = None
    return cb


def record_failure(target: str) -> CircuitState:
    cb = _get_or_create(target)
    cb.failure_count += 1
    cb.last_failure_time = time.time()
    cb.history.append({"result": "failure", "time": cb.last_failure_time})
    if cb.state == CLOSED and cb.failure_count >= cb.threshold:
        cb.state = OPEN
        cb.opened_at = time.time()
    return cb


def is_open(target: str) -> bool:
    cb = _get_or_create(target)
    if cb.state == OPEN:
        if cb.opened_at and (time.time() - cb.opened_at) >= cb.recovery_timeout:
            cb.state = HALF_OPEN
            return False
        return True
    return False


def get_state(target: str) -> dict:
    cb = _get_or_create(target)
    return {
        "target": cb.target,
        "state": cb.state,
        "failure_count": cb.failure_count,
        "success_count": cb.success_count,
        "last_failure_time": cb.last_failure_time,
        "opened_at": cb.opened_at,
        "threshold": cb.threshold,
        "recovery_timeout": cb.recovery_timeout,
    }


def configure(target: str, threshold: int = 5, recovery_timeout: float = 60.0) -> dict:
    if threshold < 1:
        raise ValueError("threshold must be >= 1")
    if recovery_timeout <= 0:
        raise ValueError("recovery_timeout must be > 0")
    cb = _get_or_create(target)
    cb.threshold = threshold
    cb.recovery_timeout = recovery_timeout
    return get_state(target)


def reset(target: str) -> None:
    if target in _circuits:
        del _circuits[target]


def reset_all() -> None:
    _circuits.clear()


def list_all() -> List[dict]:
    return [get_state(t) for t in _circuits]
