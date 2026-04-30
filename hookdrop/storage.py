"""In-memory storage for captured webhook requests."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import uuid
from datetime import datetime, timezone


@dataclass
class WebhookRequest:
    id: str
    method: str
    path: str
    headers: Dict[str, str]
    body: str
    timestamp: str
    meta: Dict[str, Any] = field(default_factory=dict)


def to_dict(req: WebhookRequest) -> Dict[str, Any]:
    return {
        "id": req.id,
        "method": req.method,
        "path": req.path,
        "headers": req.headers,
        "body": req.body,
        "timestamp": req.timestamp,
        "meta": req.meta,
    }


class RequestStore:
    def __init__(self):
        self._store: Dict[str, WebhookRequest] = {}
        self._order: List[str] = []

    def save(self, req: WebhookRequest) -> WebhookRequest:
        self._store[req.id] = req
        if req.id not in self._order:
            self._order.append(req.id)
        return req

    def get(self, request_id: str) -> Optional[WebhookRequest]:
        return self._store.get(request_id)

    def all(self) -> List[WebhookRequest]:
        return [self._store[rid] for rid in self._order if rid in self._store]

    def delete(self, request_id: str) -> bool:
        if request_id in self._store:
            del self._store[request_id]
            self._order.remove(request_id)
            return True
        return False

    def clear(self) -> None:
        self._store.clear()
        self._order.clear()

    def count(self) -> int:
        return len(self._store)

    def create_and_save(
        self,
        method: str,
        path: str,
        headers: Dict[str, str],
        body: str,
    ) -> WebhookRequest:
        req = WebhookRequest(
            id=str(uuid.uuid4()),
            method=method,
            path=path,
            headers=headers,
            body=body,
            timestamp=datetime.now(timezone.utc).isoformat(),
            meta={},
        )
        return self.save(req)
