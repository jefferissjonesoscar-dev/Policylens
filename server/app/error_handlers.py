"""
Turn every error into the same JSON shape:

    {"error": {"code": "short_code", "message": "Plain-English explanation."}}

so the frontend only has one format to handle. Technical details are logged on
the server, never sent to the browser.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import AnalysisError, InputError, RateLimitError

logger = logging.getLogger(__name__)

# HTTP status for each AnalysisError code. Anything not listed gets 502 (Bad
# Gateway), meaning "a service we depend on failed".
ANALYSIS_ERROR_STATUS = {
    "busy": 503,                  # Service Unavailable: try again shortly
    "service_unreachable": 503,
    "server_config": 500,         # our misconfiguration, not the user's fault
    "declined": 422,              # this document can't be processed
    "no_findings": 422,
}


def error_response(status: int, code: str, message: str, headers: dict | None = None) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}}, headers=headers)


def register_error_handlers(app: FastAPI) -> None:
    """Attach all handlers to the app. Called once from main.py."""

    @app.exception_handler(InputError)
    async def handle_input_error(request: Request, error: InputError) -> JSONResponse:
        return error_response(400, error.code, error.message)

    @app.exception_handler(AnalysisError)
    async def handle_analysis_error(request: Request, error: AnalysisError) -> JSONResponse:
        return error_response(ANALYSIS_ERROR_STATUS.get(error.code, 502), error.code, error.message)

    @app.exception_handler(RateLimitError)
    async def handle_rate_limit(request: Request, error: RateLimitError) -> JSONResponse:
        # Retry-After tells well-behaved clients how many seconds to wait.
        return error_response(429, error.code, error.message,
                              headers={"Retry-After": str(error.retry_after_seconds)})

    @app.exception_handler(RequestValidationError)
    async def handle_bad_request_body(request: Request, error: RequestValidationError) -> JSONResponse:
        # FastAPI's default here is a detailed technical list; replace it with one clear sentence.
        # Log where the body was wrong, but not its contents: it may hold the user's pasted text.
        logger.info("Invalid request body: %s", [(e["loc"], e["type"]) for e in error.errors()])
        expected = {
            "/api/analyze": '{"type": "text", "value": "..."}, where type is "text", "url" or "pdf"',
            "/api/permissions": '{"permissions": "..."}',
        }.get(request.url.path, "the documented format")
        return error_response(400, "invalid_request", f"The request should be JSON like {expected}.")

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, error: StarletteHTTPException) -> JSONResponse:
        # Covers 404 (unknown path) and 405 (wrong method) raised by the framework.
        messages = {404: "That page doesn't exist.", 405: "That request method isn't allowed here."}
        message = messages.get(error.status_code, "The request couldn't be completed.")
        return error_response(error.status_code, f"http_{error.status_code}", message)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, error: Exception) -> JSONResponse:
        # A bug on our side. Log the full traceback; give the user a short message.
        logger.exception("Unexpected error while handling %s %s", request.method, request.url.path)
        return error_response(500, "internal_error", "Something went wrong on our side. Please try again.")
