"""
Tests for downloading a URL, using a small web server on this machine so no
internet access is needed.

Our safety check normally refuses local addresses, so these tests replace it with
a stand-in that allows the local server and refuses any path containing
"/private". That lets us check the download logic and that redirects are checked.
"""

import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import patch

from app.errors import InputError
from app.input import url as url_module

POLICY_PARAGRAPH = "We collect your email address and share it with advertising partners. " * 5

PAGES = {
    "/policy": (200, "text/html; charset=utf-8", f"""
        <html><body>
          <nav>Home | Pricing | Blog</nav>
          <main><h1>Privacy Policy</h1><p>{POLICY_PARAGRAPH}</p><p>You can delete your account at any time.</p></main>
          <footer>Copyright 2026</footer>
        </body></html>""".encode("utf-8")),
    "/latin1": (200, "text/html", f"""<html><head><meta charset="iso-8859-1"></head>
        <body><p>Café data policy. {POLICY_PARAGRAPH}</p></body></html>""".encode("iso-8859-1")),
    "/plain": (200, "text/plain; charset=utf-8", POLICY_PARAGRAPH.encode("utf-8")),
    "/image": (200, "image/png", b"\x89PNG not really an image"),
    "/empty": (200, "text/html", b"<html><body><div id='app'></div><script>render()</script></body></html>"),
    "/forbidden": (403, "text/html", b"Forbidden"),
    "/missing": (404, "text/html", b"Not found"),
    "/huge": (200, "text/html", b"<p>" + b"x" * (url_module.MAX_DOWNLOAD_BYTES + 10) + b"</p>"),
}

REDIRECTS = {
    "/old-policy": "/policy",
    "/sneaky": "/private/admin",
}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in REDIRECTS:
            self.send_response(302)
            self.send_header("Location", REDIRECTS[self.path])
            self.end_headers()
            return
        status, content_type, body = PAGES.get(self.path, (404, "text/plain", b"Not found"))
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # keep test output quiet
        pass


def _allow_local_except_private(url: str) -> None:
    if "/private" in url:
        raise InputError("url_not_allowed", "blocked by test")


class FetchUrlTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def setUp(self):
        patcher = patch.object(url_module, "check_url_is_public", _allow_local_except_private)
        patcher.start()
        self.addCleanup(patcher.stop)
        # Make sure a proxy set in the environment doesn't intercept requests to the local server.
        env = patch.dict("os.environ", {"NO_PROXY": "127.0.0.1", "no_proxy": "127.0.0.1"})
        env.start()
        self.addCleanup(env.stop)

    def assert_error(self, path, code):
        with self.assertRaises(InputError) as caught:
            url_module.text_from_url(self.base + path)
        self.assertEqual(caught.exception.code, code)

    def test_html_page_returns_main_text_only(self):
        text = url_module.text_from_url(self.base + "/policy")
        self.assertTrue(text.startswith("Privacy Policy"))
        self.assertIn("You can delete your account at any time.", text)
        self.assertNotIn("Pricing", text)
        self.assertNotIn("Copyright", text)

    def test_charset_from_meta_tag_is_used(self):
        self.assertIn("Café data policy.", url_module.text_from_url(self.base + "/latin1"))

    def test_plain_text_page_is_accepted(self):
        self.assertEqual(url_module.text_from_url(self.base + "/plain"), POLICY_PARAGRAPH.strip())

    def test_safe_redirect_is_followed(self):
        self.assertIn("You can delete your account", url_module.text_from_url(self.base + "/old-policy"))

    def test_redirect_target_is_checked(self):
        self.assert_error("/sneaky", "url_not_allowed")

    def test_non_text_content_is_rejected(self):
        self.assert_error("/image", "url_unsupported_type")

    def test_javascript_only_page_gives_helpful_error(self):
        self.assert_error("/empty", "url_no_text")

    def test_http_errors_are_explained(self):
        self.assert_error("/forbidden", "url_blocked")
        self.assert_error("/missing", "url_http_error")

    def test_oversized_page_is_rejected(self):
        self.assert_error("/huge", "url_too_large")


if __name__ == "__main__":
    unittest.main()
