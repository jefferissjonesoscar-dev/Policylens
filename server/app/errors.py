"""
Error types with plain-English messages for the user.

InputError: a problem with what the user submitted (bad URL, empty text).
AnalysisError: the analysis step failed (Claude unreachable, answer failed our checks).
RateLimitError: this visitor (or everyone, for the daily cap) has sent too many requests.

Each error carries a short machine-readable code and a plain-English message.
app/error_handlers.py turns them into JSON responses of the form
{"error": {"code": ..., "message": ...}}.
"""


class InputError(Exception):
    """A problem with what the user submitted, explained in plain English."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class AnalysisError(Exception):
    """The analysis could not be completed, explained in plain English."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class RateLimitError(Exception):
    """Too many requests from one visitor in the current time window."""

    def __init__(self, retry_after_seconds: int, message: str | None = None) -> None:
        minutes = max(1, round(retry_after_seconds / 60))
        if message is None:
            message = f"You've reached the limit of analyses for now. Please try again in about {minutes} minute(s)."
        super().__init__(message)
        self.code = "rate_limited"
        self.message = message
        self.retry_after_seconds = retry_after_seconds
