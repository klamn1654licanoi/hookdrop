"""In-memory storage for captured webhook requests."""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WebhookRequest:
    id: str
    method: str
    path: str
    headers: dict
    query_params: dict
    body: bytes
    received_at: datetime
    content_type: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "method": self.method,
            "path": self.path,
            "headers": dict(self.headers),
            "query_params": dict(self.query_params),
            "body": self.body.decode("utf-8", errors="replace"),
            "received_at": self.received_at.isoformat(),
            "content_type": self.content_type,
        }


class RequestStore:
    """Thread-safe in-memory store for webhook requests."""

    def __init__(self, max_size: int = 200):
        self._requests: list[WebhookRequest] = []
        self._max_size = max_size

    def save(self, method: str, path: str, headers: dict,
             query_params: dict, body: bytes) -> WebhookRequest:
        req = WebhookRequest(
            id=str(uuid.uuid4()),
            method=method.upper(),
            path=path,
            headers=dict(headers),
            query_params=dict(query_params),
            body=body,
            received_at=datetime.now(timezone.utc),
            content_type=headers.get("content-type"),
        )
        self._requests.append(req)
        if len(self._requests) > self._max_size:
            self._requests.pop(0)
        return req

    def all(self) -> list[WebhookRequest]:
        return list(reversed(self._requests))

    def get(self, request_id: str) -> Optional[WebhookRequest]:
        return next((r for r in self._requests if r.id == request_id), None)

    def delete(self, request_id: str) -> bool:
        before = len(self._requests)
        self._requests = [r for r in self._requests if r.id != request_id]
        return len(self._requests) < before

    def clear(self) -> int:
        count = len(self._requests)
        self._requests.clear()
        return count

    def __len__(self) -> int:
        return len(self._requests)
