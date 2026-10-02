"""
Fetch a policy from a URL and return its readable text.

Uses Python's built-in urllib, so no extra library is needed.

Safety: because the server fetches whatever URL a user types, it could be
tricked into reading internal addresses (localhost, cloud metadata services,
private networks). This is called server-side request forgery (SSRF). We block
it by resolving the hostname and refusing any address that is not public, and we
re-check every redirect. One gap remains: urllib resolves the hostname again when
it connects, so a DNS server that changes its answer between the two lookups
(a "DNS rebinding" attack) could slip through. Closing that gap needs connecting
to the already-checked IP address, which is more code than an MVP warrants;
running the app with no access to internal services is the backstop.
"""

import ipaddress
import re
import socket
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from app.errors import InputError
from app.input.html_extract import extract_main_text
from app.input.pdf import text_from_pdf_bytes
from app.input.text import MIN_CHARS, normalize_text

TIMEOUT_SECONDS = 15
MAX_DOWNLOAD_BYTES = 5 * 1024 * 1024  # 5 MB is far larger than any normal policy page
MAX_REDIRECTS = 5

# Identify ourselves honestly. Some sites block non-browser visitors; for those
# the user gets a message suggesting they paste the text instead.
USER_AGENT = "PolicyLens/0.1 (privacy policy summarizer)"

HTML_TYPES = {"text/html", "application/xhtml+xml"}

# Finds <meta charset="..."> (or the older http-equiv form) near the top of a page.
_META_CHARSET = re.compile(rb"""<meta[^>]+charset=["']?([\w-]+)""", re.IGNORECASE)


@dataclass
class FetchedPage:
    body: bytes
    content_type: str   # e.g. "text/html"
    charset: str | None  # from the Content-Type header, if the server sent one


def check_url_is_public(url: str) -> None:
    """Raise InputError unless the URL is http(s) and its host resolves only to public addresses."""
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise InputError("invalid_url", "The link must start with http:// or https://.")
    if not parts.hostname:
        raise InputError("invalid_url", "That doesn't look like a complete web address.")

    try:
        port = parts.port or (443 if parts.scheme == "https" else 80)
    except ValueError:
        raise InputError("invalid_url", "That web address has an invalid port number.")

    try:
        addresses = socket.getaddrinfo(parts.hostname, port, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise InputError("url_not_found", f"Couldn't find the website {parts.hostname}. Check the address.")

    for *_, sockaddr in addresses:
        # IPv6 link-local addresses can carry a "%interface" suffix; drop it before parsing.
        ip = ipaddress.ip_address(sockaddr[0].split("%")[0])
        if not ip.is_global:
            raise InputError("url_not_allowed", "That address points to a private network and can't be fetched.")


class _SafeRedirectHandler(HTTPRedirectHandler):
    """Follows redirects like normal, but checks each new address first."""

    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url_is_public(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_url(url: str) -> FetchedPage:
    """Download a URL with safety checks, a timeout and a size cap."""
    url = url.strip()
    check_url_is_public(url)

    opener = build_opener(_SafeRedirectHandler)
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain;q=0.9,application/pdf;q=0.8,*/*;q=0.5"})

    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            # Read one byte past the limit so we can tell "exactly at the limit" from "too big".
            body = response.read(MAX_DOWNLOAD_BYTES + 1)
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset()
    except HTTPError as error:
        error.close()  # an HTTPError holds the open connection; release it
        if error.code in (401, 403):
            raise InputError(
                "url_blocked",
                f"The website refused the request (HTTP {error.code}). Copy the policy text and paste it instead.",
            )
        raise InputError("url_http_error", f"The website returned an error (HTTP {error.code}). Check the address.")
    except URLError as error:
        if isinstance(error.reason, TimeoutError):
            raise InputError("url_timeout", "The website took too long to respond. Try again or paste the text.")
        raise InputError("url_unreachable", "Couldn't connect to that website. Check the address or paste the text.")
    except TimeoutError:
        raise InputError("url_timeout", "The website took too long to respond. Try again or paste the text.")

    if len(body) > MAX_DOWNLOAD_BYTES:
        raise InputError("url_too_large", "That page is too large to analyse (over 5 MB).")

    return FetchedPage(body=body, content_type=content_type, charset=charset)


def _decode(page: FetchedPage) -> str:
    """Turn the downloaded bytes into a string using the page's declared encoding, or UTF-8."""
    charset = page.charset
    if not charset:
        match = _META_CHARSET.search(page.body[:4096])
        charset = match.group(1).decode("ascii") if match else "utf-8"
    try:
        return page.body.decode(charset, errors="replace")
    except LookupError:  # the page named an encoding Python doesn't know
        return page.body.decode("utf-8", errors="replace")


def text_from_url(url: str) -> str:
    """Fetch a URL and return the policy text found on it."""
    page = fetch_url(url)

    if page.content_type in HTML_TYPES:
        text = extract_main_text(_decode(page))
    elif page.content_type == "text/plain":
        text = normalize_text(_decode(page))
    elif page.content_type == "application/pdf":
        return text_from_pdf_bytes(page.body)  # does its own "no text found" check
    else:
        raise InputError(
            "url_unsupported_type",
            f"That link returns a file of type {page.content_type}, not a web page. "
            "Copy the text and paste it instead.",
        )

    if len(text) < MIN_CHARS:
        raise InputError(
            "url_no_text",
            "Couldn't find the policy text on that page. It may load its content with "
            "JavaScript. Copy the text from your browser and paste it instead.",
        )
    return text
