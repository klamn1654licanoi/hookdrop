"""Export webhook requests to various formats (JSON, curl commands)."""

import json
import shlex
from typing import List
from hookdrop.storage import WebhookRequest


def to_json(requests: List[WebhookRequest], indent: int = 2) -> str:
    """Serialize a list of WebhookRequest objects to a JSON string."""
    return json.dumps([r.to_dict() for r in requests], indent=indent, default=str)


def to_curl(request: WebhookRequest, target_url: str = None) -> str:
    """Convert a WebhookRequest to an equivalent curl command string."""
    url = target_url or f"http://localhost:9000{request.path}"
    parts = ["curl", "-s", "-X", request.method]

    for key, value in request.headers.items():
        lower_key = key.lower()
        if lower_key in ("host", "content-length"):
            continue
        parts += ["-H", f"{key}: {value}"]

    if request.body:
        parts += ["--data-raw", request.body]

    parts.append(url)
    return " ".join(shlex.quote(p) for p in parts)


def to_curl_all(requests: List[WebhookRequest], target_url: str = None) -> str:
    """Convert multiple WebhookRequests to curl commands, one per line."""
    return "\n".join(to_curl(r, target_url) for r in requests)
