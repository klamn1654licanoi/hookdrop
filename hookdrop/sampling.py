"""Request sampling — keep only a percentage of incoming requests."""

import random
from typing import Optional
from hookdrop.storage import RequestStore, WebhookRequest

_sampling_rate: float = 1.0  # 1.0 = 100%, 0.0 = 0%


def set_sampling_rate(rate: float) -> None:
    """Set the global sampling rate (0.0 to 1.0)."""
    global _sampling_rate
    if not (0.0 <= rate <= 1.0):
        raise ValueError(f"Sampling rate must be between 0.0 and 1.0, got {rate}")
    _sampling_rate = rate


def get_sampling_rate() -> float:
    """Return the current sampling rate."""
    return _sampling_rate


def reset_sampling_rate() -> None:
    """Reset sampling rate to 100% (no sampling)."""
    global _sampling_rate
    _sampling_rate = 1.0


def should_sample() -> bool:
    """Return True if the current request should be kept based on sampling rate."""
    return random.random() < _sampling_rate


def sample_requests(store: RequestStore, rate: Optional[float] = None) -> list[WebhookRequest]:
    """Return a sampled subset of all stored requests.

    Uses the provided rate or falls back to the global sampling rate.
    """
    effective_rate = rate if rate is not None else _sampling_rate
    if not (0.0 <= effective_rate <= 1.0):
        raise ValueError(f"Sampling rate must be between 0.0 and 1.0, got {effective_rate}")
    all_requests = store.get_all()
    if effective_rate >= 1.0:
        return all_requests
    if effective_rate <= 0.0:
        return []
    return [r for r in all_requests if random.random() < effective_rate]


def sampling_summary(store: RequestStore) -> dict:
    """Return a summary of sampling configuration and store stats."""
    total = len(store.get_all())
    rate = get_sampling_rate()
    return {
        "sampling_rate": rate,
        "sampling_percent": round(rate * 100, 2),
        "total_requests": total,
        "expected_sampled": round(total * rate),
    }
