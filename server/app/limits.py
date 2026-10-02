"""
Size limits and rate limiting for the API.

The rate limiter is a small in-memory "sliding window": for each visitor (by IP
address) we remember the times of their recent requests and refuse a new one if
there are already too many in the window. It's written by hand instead of using a
library because it's about 30 lines.

Two limitations to know about:
  - Counts live in this process's memory, so they reset when the server restarts,
    and each server process keeps its own counts if you run several.
  - Behind a reverse proxy or load balancer every request appears to come from the
    proxy's IP. Uvicorn's --proxy-headers and --forwarded-allow-ips options make it
    use the real visitor IP from the proxy's X-Forwarded-For header instead.
"""

import threading
import time
from collections import defaultdict, deque

from fastapi import Request

from app.errors import RateLimitError

# Largest request body we accept. The biggest legitimate body is a 10 MB PDF,
# which base64 encoding turns into about 13.4 MB of text, plus the JSON around it.
# Pasted text has its own, smaller limit (MAX_TEXT_CHARS).
MAX_BODY_BYTES = 14 * 1024 * 1024  # 14 MB

# Longest document we analyse. Typical policies are 20,000-80,000 characters; this
# allows long terms of service while keeping the cost of one request bounded.
MAX_TEXT_CHARS = 300_000

# Browsers and servers commonly cap URLs around 2,000 characters.
MAX_URL_CHARS = 2_048

# Each analysis makes one or more paid API calls, so keep this modest.
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 15 * 60


class SlidingWindowRateLimiter:
    """Allows at most max_requests per key within any window_seconds period."""

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        # FastAPI runs our (non-async) route functions on several threads at once,
        # so the shared dictionary needs a lock.
        self._lock = threading.Lock()

    def check(self, key: str, now: float | None = None) -> None:
        """Record a request for this key, or raise RateLimitError if it's over the limit."""
        now = time.monotonic() if now is None else now
        with self._lock:
            timestamps = self._requests[key]
            # Forget requests that have slid out of the window.
            while timestamps and timestamps[0] <= now - self.window_seconds:
                timestamps.popleft()

            if len(timestamps) >= self.max_requests:
                retry_after = int(timestamps[0] + self.window_seconds - now) + 1
                raise RateLimitError(retry_after)

            timestamps.append(now)


analyze_rate_limiter = SlidingWindowRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)


def limit_analyze_requests(request: Request) -> None:
    """FastAPI dependency: apply the rate limit to the caller's IP address."""
    client_ip = request.client.host if request.client else "unknown"
    analyze_rate_limiter.check(client_ip)
