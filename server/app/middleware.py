"""
Reject oversized request bodies before reading them.

FastAPI reads and parses the whole body before our route code runs, so a size
check inside the route would come too late to protect memory. This middleware
looks at the Content-Length header first:
  - no Content-Length on a request with a body (e.g. chunked upload) -> 411
  - Content-Length over the limit -> 413
Uvicorn never reads more bytes than Content-Length declares, so checking the
header is enough.
"""

import json

from app.limits import MAX_BODY_BYTES

_METHODS_WITH_BODY = {"POST", "PUT", "PATCH"}


class BodySizeLimitMiddleware:
    """Plain ASGI middleware (no extra library needed)."""

    def __init__(self, app, max_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in _METHODS_WITH_BODY:
            await self.app(scope, receive, send)
            return

        headers = dict(scope["headers"])
        length_header = headers.get(b"content-length")

        if length_header is None or not length_header.isdigit():
            await _send_error(send, 411, "length_required",
                              "The request must include its size (Content-Length header).")
            return
        if int(length_header) > self.max_bytes:
            limit_mb = self.max_bytes / (1024 * 1024)
            await _send_error(send, 413, "request_too_large",
                              f"That's too much data to send at once (limit {limit_mb:g} MB).")
            return

        await self.app(scope, receive, send)


async def _send_error(send, status: int, code: str, message: str) -> None:
    """Send a JSON error in our standard shape without involving FastAPI."""
    body = json.dumps({"error": {"code": code, "message": message}}).encode("utf-8")
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
        ],
    })
    await send({"type": "http.response.body", "body": body})
