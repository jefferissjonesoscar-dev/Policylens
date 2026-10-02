"""
Check that a quote really appears in the source document.

This is what makes the summary verifiable: a bullet is only shown with a quote we
found in the text ourselves, not one we trust the model to have copied correctly.

The match is exact apart from differences a reader wouldn't notice: runs of
whitespace and line breaks, curly vs straight quote marks, and dash styles.
Everything else, including capitalisation and wording, must match.
"""

import re
import unicodedata

# Characters that look alike and are often swapped when text is copied.
_LOOKALIKES = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "′": "'",   # single quotes
    "“": '"', "”": '"', "„": '"', "″": '"',   # double quotes
    "‐": "-", "‑": "-", "‒": "-", "–": "-",   # hyphens and dashes
    "—": "-", "−": "-",
    " ": " ",                                               # non-breaking space
})

_WHITESPACE = re.compile(r"\s+")


def normalize_for_match(text: str) -> str:
    """Make text comparable: same character forms, same quote marks and dashes, single spaces."""
    text = unicodedata.normalize("NFKC", text).translate(_LOOKALIKES)
    return _WHITESPACE.sub(" ", text).strip()


def quote_in_source(quote: str, normalized_source: str) -> bool:
    """True if the quote appears in the source.

    normalized_source must already be passed through normalize_for_match. Doing
    that once per document, rather than once per quote, keeps this fast.
    """
    normalized_quote = normalize_for_match(quote)
    return bool(normalized_quote) and normalized_quote in normalized_source
