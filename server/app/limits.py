"""
Size limits and rate limiting for the API.

The rate limiter is a small in-memory "sliding window": for each visitor (by IP
address) we remember the times of their recent requests and refuse a new one if
there are already too many in the window. It's written by hand instead of using a
library because it's about 30 lines.

There are two limiters: one per visitor, and one server-wide daily cap that
bounds the total Claude bill.

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

from app.config import settings
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


# Spending cap: the most analyses the whole server runs per 24 hours, for everyone
# combined (set with DAILY_ANALYSIS_LIMIT). The per-IP limit above stops one visitor
# hogging the service; this one bounds the total Claude bill even if many visitors
# (or one visitor faking many IP addresses) use it at once.
DAILY_WINDOW_SECONDS = 24 * 60 * 60
DAILY_LIMIT_MESSAGE = ("PolicyLens has reached its daily limit of analyses. "
                       "Please try again tomorrow.")


class SlidingWindowRateLimiter:
    """Allows at most max_requests per key within any window_seconds period."""

    def __init__(self, max_requests: int, window_seconds: float, message: str | None = None) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.message = message  # None means RateLimitError's default wording
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
                raise RateLimitError(retry_after, self.message)

            timestamps.append(now)


analyze_rate_limiter = SlidingWindowRateLimiter(RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW_SECONDS)
daily_rate_limiter = SlidingWindowRateLimiter(
    settings.daily_analysis_limit, DAILY_WINDOW_SECONDS, DAILY_LIMIT_MESSAGE)


def limit_analyze_requests(request: Request) -> None:
    """FastAPI dependency: apply the per-IP limit, then the server-wide daily cap."""
    client_ip = request.client.host if request.client else "unknown"
    analyze_rate_limiter.check(client_ip)
    # One shared key, so every visitor counts towards the same daily total.
    daily_rate_limiter.check("everyone")
