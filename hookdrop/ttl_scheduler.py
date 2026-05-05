"""Background scheduler for automatic TTL-based expiry of webhook requests."""

import threading
import logging
from hookdrop.storage import RequestStore
from hookdrop.ttl import expire_requests

logger = logging.getLogger(__name__)


class TTLScheduler:
    """Runs a background thread that periodically expires old requests."""

    def __init__(self, store: RequestStore, ttl_seconds: int = 3600, interval: int = 60):
        self.store = store
        self.ttl_seconds = ttl_seconds
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def _run(self):
        while not self._stop_event.wait(self.interval):
            try:
                removed = expire_requests(self.store, self.ttl_seconds)
                if removed:
                    logger.info(
                        "TTLScheduler: expired %d request(s): %s",
                        len(removed),
                        removed,
                    )
            except Exception as exc:
                logger.error("TTLScheduler error: %s", exc)

    def start(self):
        """Start the background expiry thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="ttl-scheduler")
        self._thread.start()
        logger.info(
            "TTLScheduler started (ttl=%ds, interval=%ds)",
            self.ttl_seconds,
            self.interval,
        )

    def stop(self):
        """Stop the background expiry thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("TTLScheduler stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
