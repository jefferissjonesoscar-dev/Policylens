"""
Tests for Stage 4: the HTTP API, limits and error format.

The real app runs on a local port in a background thread and we call it with
Python's built-in http.client, so no extra test library is needed. The analysis
step is replaced with a stand-in, so no API calls are made.
"""

import base64
import http.client
import json
import socket
import threading
import time
import unittest
from unittest.mock import patch

import uvicorn

from app import limits
from app.errors import AnalysisError, RateLimitError
from app.limits import MAX_TEXT_CHARS, SlidingWindowRateLimiter
from app.main import app
from app.routes import analyze as analyze_route
from tests.pdf_helpers import make_pdf

POLICY_TEXT = "We collect your email address and share it with advertising partners. " * 5
FAKE_RESULT = {"bullets": [], "risk_level": "Medium", "risk_reason": "Shares data with advertisers."}


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = _free_port()
        # log_level="critical" hides uvicorn's own copy of the traceback in the
        # unexpected-error test; our handler's log is checked in that test instead.
        config = uvicorn.Config(app, host="127.0.0.1", port=cls.port, log_level="critical")
        cls.server = uvicorn.Server(config)
        cls.thread = threading.Thread(target=cls.server.run, daemon=True)
        cls.thread.start()
        deadline = time.time() + 10
        while not cls.server.started:
            if time.time() > deadline:
                raise RuntimeError("Test server didn't start")
            time.sleep(0.05)

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.thread.join(timeout=10)

    def setUp(self):
        # A fresh, generous rate limiter for each test so tests don't affect each other.
        limiter = patch.object(limits, "analyze_rate_limiter", SlidingWindowRateLimiter(100, 60))
        limiter.start()
        self.addCleanup(limiter.stop)
        daily = patch.object(limits, "daily_rate_limiter", SlidingWindowRateLimiter(100, 60))
        daily.start()
        self.addCleanup(daily.stop)
        # Replace the paid analysis step with a stand-in that records what it was given.
        self.analyzed_texts = []

        def fake_analyze(text):
            self.analyzed_texts.append(text)
            return FAKE_RESULT

        analysis = patch.object(analyze_route, "analyze_policy", side_effect=fake_analyze)
        self.fake_analysis = analysis.start()
        self.addCleanup(analysis.stop)

    def request(self, method, path, body=None, headers=None):
        """Send a request and return (status, parsed JSON body, response headers)."""
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            if isinstance(body, dict):
                body = json.dumps(body).encode("utf-8")
                headers = {"Content-Type": "application/json", **(headers or {})}
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            return response.status, json.loads(response.read()), dict(response.getheaders())
        finally:
            conn.close()

    def assert_error(self, status, body, expected_status, expected_code):
        self.assertEqual(status, expected_status, body)
        self.assertEqual(body["error"]["code"], expected_code)
        self.assertTrue(body["error"]["message"])

    # --- Happy paths ---

    def test_health(self):
        status, body, _ = self.request("GET", "/api/health")
        self.assertEqual((status, body), (200, {"status": "ok"}))

    def test_analyze_pasted_text(self):
        status, body, _ = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})
        self.assertEqual((status, body), (200, FAKE_RESULT))
        self.assertEqual(self.analyzed_texts, [POLICY_TEXT.strip()])

    # --- Input problems ---

    def test_short_text_is_rejected(self):
        status, body, _ = self.request("POST", "/api/analyze", {"type": "text", "value": "Too short."})
        self.assert_error(status, body, 400, "text_too_short")

    def test_text_over_the_length_limit_is_rejected(self):
        status, body, _ = self.request("POST", "/api/analyze", {"type": "text", "value": "a" * (MAX_TEXT_CHARS + 1)})
        self.assert_error(status, body, 400, "text_too_long")
        self.fake_analysis.assert_not_called()

    def test_private_url_is_rejected(self):
        status, body, _ = self.request("POST", "/api/analyze", {"type": "url", "value": "http://127.0.0.1/admin"})
        self.assert_error(status, body, 400, "url_not_allowed")

    def test_analyze_pdf(self):
        pdf = make_pdf([[POLICY_TEXT[:70], POLICY_TEXT[70:140]], [POLICY_TEXT[140:]]])
        encoded = base64.b64encode(pdf).decode("ascii")
        status, body, _ = self.request("POST", "/api/analyze", {"type": "pdf", "value": encoded})
        self.assertEqual((status, body), (200, FAKE_RESULT))
        self.assertIn("advertising partners", self.analyzed_texts[0])

    def test_explain_permissions(self):
        status, body, _ = self.request("POST", "/api/permissions", {"permissions": "CAMERA\nREAD_SMS"})
        self.assertEqual(status, 200)
        self.assertEqual([p["name"] for p in body["permissions"]],
                         ["android.permission.READ_SMS", "android.permission.CAMERA"])

    def test_malformed_request_gets_one_clear_message(self):
        for bad_body in ({"type": "word", "value": "x"}, {"value": "x"}, b"not json"):
            with self.subTest(body=bad_body):
                headers = {"Content-Type": "application/json"}
                with self.assertLogs("app.error_handlers", level="INFO"):
                    status, body, _ = self.request("POST", "/api/analyze", bad_body, headers)
                self.assert_error(status, body, 400, "invalid_request")

    # --- Size limits ---

    def test_oversized_body_is_rejected_before_reading(self):
        status, body, _ = self.request("POST", "/api/analyze", b"x" * (limits.MAX_BODY_BYTES + 1),
                                       {"Content-Type": "application/json"})
        self.assert_error(status, body, 413, "request_too_large")

    def test_body_without_a_length_is_rejected(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        try:
            # encode_chunked sends the body without a Content-Length header.
            conn.request("POST", "/api/analyze", body=iter([b'{"type": "text"}']),
                         headers={"Content-Type": "application/json"}, encode_chunked=True)
            response = conn.getresponse()
            self.assert_error(response.status, json.loads(response.read()), 411, "length_required")
        finally:
            conn.close()

    # --- Rate limiting ---

    def test_rate_limit_returns_429_with_retry_after(self):
        with patch.object(limits, "analyze_rate_limiter", SlidingWindowRateLimiter(2, 600)):
            for _ in range(2):
                status, _, _ = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})
                self.assertEqual(status, 200)
            status, body, headers = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})

        self.assert_error(status, body, 429, "rate_limited")
        self.assertTrue(0 < int(headers["retry-after"]) <= 600)

    def test_daily_cap_applies_to_everyone_combined(self):
        cap = SlidingWindowRateLimiter(1, limits.DAILY_WINDOW_SECONDS, limits.DAILY_LIMIT_MESSAGE)
        with patch.object(limits, "daily_rate_limiter", cap):
            status, _, _ = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})
            self.assertEqual(status, 200)
            status, body, _ = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})

        self.assert_error(status, body, 429, "rate_limited")
        self.assertIn("daily limit", body["error"]["message"])

    # --- Errors from later steps ---

    def test_analysis_errors_keep_their_message(self):
        self.fake_analysis.side_effect = AnalysisError("busy", "The analysis service is busy right now.")
        status, body, _ = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})
        self.assert_error(status, body, 503, "busy")
        self.assertEqual(body["error"]["message"], "The analysis service is busy right now.")

    def test_unexpected_errors_hide_details(self):
        self.fake_analysis.side_effect = KeyError("secret internal detail")
        with self.assertLogs("app.error_handlers", level="ERROR"):
            status, body, _ = self.request("POST", "/api/analyze", {"type": "text", "value": POLICY_TEXT})
        self.assert_error(status, body, 500, "internal_error")
        self.assertNotIn("secret", json.dumps(body))

    def test_unknown_path_uses_the_same_error_format(self):
        status, body, _ = self.request("GET", "/api/nope")
        self.assert_error(status, body, 404, "http_404")


class SlidingWindowRateLimiterTests(unittest.TestCase):
    def test_allows_up_to_the_limit_then_blocks(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        for second in (0, 1, 2):
            limiter.check("1.2.3.4", now=second)
        with self.assertRaises(RateLimitError) as caught:
            limiter.check("1.2.3.4", now=3)
        # The oldest request (at second 0) leaves the window at second 60.
        self.assertEqual(caught.exception.retry_after_seconds, 58)

    def test_requests_slide_out_of_the_window(self):
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
        limiter.check("1.2.3.4", now=0)
        limiter.check("1.2.3.4", now=60)  # the first request has expired

    def test_each_visitor_has_their_own_count(self):
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
        limiter.check("1.1.1.1", now=0)
        limiter.check("2.2.2.2", now=0)


if __name__ == "__main__":
    unittest.main()
