"""
POST /api/analyze: the main endpoint.

Request body (JSON):
    {"type": "text", "value": "<the policy text>"}
    {"type": "url",  "value": "https://example.com/privacy"}
    {"type": "pdf",  "value": "<the PDF file, base64-encoded>"}

Response: the summary JSON described in CLAUDE.md, or an error in the shape
{"error": {"code": ..., "message": ...}}.

PDFs are sent as base64 text inside the JSON rather than as a file upload. That
makes the file about a third bigger in transit, but it keeps one simple request
format and avoids the extra python-multipart library that file uploads need.
"""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.analysis.analyze import analyze_policy
from app.errors import InputError
from app.input.pdf import text_from_pdf_base64
from app.input.text import clean_pasted_text
from app.input.url import text_from_url
from app.limits import MAX_TEXT_CHARS, MAX_URL_CHARS, limit_analyze_requests

router = APIRouter()


class AnalyzeRequest(BaseModel):
    type: Literal["text", "url", "pdf"]
    value: str


def extract_text(request: AnalyzeRequest) -> str:
    """Turn the request into clean policy text, checking the size limits."""
    if request.type == "text":
        # Checked before cleaning so we never process an oversized paste.
        if len(request.value) > MAX_TEXT_CHARS:
            raise InputError("text_too_long", _too_long_message(len(request.value)))
        text = clean_pasted_text(request.value)

    elif request.type == "url":
        if len(request.value) > MAX_URL_CHARS:
            raise InputError("invalid_url", "That web address is too long.")
        text = text_from_url(request.value)

    else:
        text = text_from_pdf_base64(request.value)

    # A fetched page can be longer than anything a user would paste.
    if len(text) > MAX_TEXT_CHARS:
        raise InputError("text_too_long", _too_long_message(len(text)))
    return text


def _too_long_message(length: int) -> str:
    return (f"That document is {length:,} characters long; the limit is {MAX_TEXT_CHARS:,}. "
            "Try pasting just the privacy or data section.")


# A plain "def" (not "async def") on purpose: fetching the URL and calling Claude
# block while they wait, so FastAPI runs this function on a worker thread and the
# server stays responsive to other requests meanwhile.
@router.post("/api/analyze", dependencies=[Depends(limit_analyze_requests)])
def analyze(request: AnalyzeRequest) -> dict:
    text = extract_text(request)
    return analyze_policy(text)
