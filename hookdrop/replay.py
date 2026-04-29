import httpx
from typing import Optional
from hookdrop.storage import WebhookRequest


def build_replay_request(request: WebhookRequest, target_url: str) -> dict:
    """Build a replay request dict from a stored WebhookRequest."""
    return {
        "method": request.method,
        "url": target_url,
        "headers": {
            k: v
            for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        },
        "content": request.body.encode() if isinstance(request.body, str) else request.body,
    }


def replay_request(
    request: WebhookRequest,
    target_url: str,
    timeout: float = 10.0,
) -> dict:
    """
    Replay a stored webhook request to a target URL.

    Returns a dict with status_code, headers, body, and error (if any).
    """
    result = {
        "request_id": request.id,
        "target_url": target_url,
        "status_code": None,
        "response_headers": {},
        "response_body": "",
        "error": None,
    }

    try:
        replay = build_replay_request(request, target_url)
        with httpx.Client(timeout=timeout) as client:
            response = client.request(**replay)
        result["status_code"] = response.status_code
        result["response_headers"] = dict(response.headers)
        result["response_body"] = response.text
    except httpx.TimeoutException as exc:
        result["error"] = f"Request timed out: {exc}"
    except httpx.RequestError as exc:
        result["error"] = f"Request error: {exc}"

    return result
