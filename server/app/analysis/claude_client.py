"""
One place that talks to the Claude API.

ask_claude_for_json() sends a system prompt and a user message, asks for a reply
in a fixed JSON shape (structured output), and returns the parsed JSON. Any API
problem becomes an AnalysisError with a message the user can understand; the
technical details go to the server log only.
"""

import json
import logging
from functools import lru_cache

import anthropic

from app.config import settings
from app.errors import AnalysisError

logger = logging.getLogger(__name__)

# The reply is a short JSON object, but the model also thinks before answering,
# and those thinking tokens count toward this limit.
MAX_TOKENS = 16_000

# How much reasoning effort to spend. "medium" is enough for reading and
# summarising; raise it to "high" if quality checks show it helps.
EFFORT = "medium"

# Seconds to wait for one API call before giving up (the SDK then retries).
TIMEOUT_SECONDS = 120

# If the model declines a request under its safety rules, the API re-runs it on
# a suitable fallback model instead of returning nothing. This is a beta feature,
# so it needs the beta flag below.
FALLBACK_BETA = "server-side-fallback-2026-07-01"


class InvalidReplyError(Exception):
    """Claude's reply couldn't be parsed. The caller decides whether to retry."""


@lru_cache(maxsize=1)
def _client() -> anthropic.Anthropic:
    """Create the API client once and reuse it (it keeps connections open between calls)."""
    # The SDK automatically retries rate limits, timeouts and server errors twice.
    return anthropic.Anthropic(api_key=settings.anthropic_api_key, timeout=TIMEOUT_SECONDS)


def ask_claude_for_json(system: str, user_message: str, schema: dict) -> dict:
    """Send one request and return Claude's reply as a dict matching the schema."""
    try:
        response = _client().beta.messages.create(
            model=settings.anthropic_model,
            max_tokens=MAX_TOKENS,
            system=system,
            messages=[{"role": "user", "content": user_message}],
            output_config={
                "effort": EFFORT,
                "format": {"type": "json_schema", "schema": schema},
            },
            betas=[FALLBACK_BETA],
            fallbacks="default",
        )
    except anthropic.AuthenticationError:
        logger.error("Anthropic API rejected the API key")
        raise AnalysisError("server_config", "The server's API key isn't valid. Please contact the site owner.")
    except anthropic.RateLimitError:
        raise AnalysisError("busy", "The analysis service is busy right now. Please try again in a minute.")
    except (anthropic.APIConnectionError, anthropic.APITimeoutError):
        # APITimeoutError is a kind of APIConnectionError; both are listed to make the intent clear.
        raise AnalysisError("service_unreachable", "Couldn't reach the analysis service. Please try again.")
    except anthropic.APIStatusError as error:
        logger.error("Anthropic API error %s: %s", error.status_code, error.message)
        raise AnalysisError("service_error", "The analysis service had a problem. Please try again.")

    if response.stop_reason == "refusal":
        category = response.stop_details.category if response.stop_details else None
        logger.warning("Request declined (category=%s, request_id=%s)", category, response._request_id)
        raise AnalysisError("declined", "This document couldn't be analysed. Try a different policy.")
    if response.stop_reason == "max_tokens":
        logger.warning("Reply cut off at max_tokens (request_id=%s)", response._request_id)
        raise AnalysisError("too_long", "The analysis ran out of room before finishing. Please try again.")

    # With structured output the reply's text block is the JSON. Other blocks
    # (the model's thinking, a fallback marker) are skipped.
    text = next((block.text for block in response.content if block.type == "text"), "")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Shouldn't happen with structured output, but the caller retries once if it does.
        logger.warning("Reply was not valid JSON (request_id=%s)", response._request_id)
        raise InvalidReplyError("The reply was not valid JSON.")
