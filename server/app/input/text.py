"""
Clean up raw text so every input type (paste, web page, PDF) looks the same
before analysis.

Paragraph breaks are kept on purpose: the chunker splits on them, and they make
quotes easier to read in the results.
"""

import re
import unicodedata

from app.errors import InputError

# Anything shorter than this is very unlikely to be a full policy.
MIN_CHARS = 200

# Zero-width and byte-order-mark characters that are invisible but would break
# exact quote matching.
_INVISIBLE = re.compile("[​‌‍⁠﻿]")


def normalize_text(raw: str) -> str:
    """Return tidy text: consistent line endings, no runs of spaces, at most one blank line in a row."""
    # NFKC turns lookalike characters (e.g. non-breaking spaces, full-width letters) into plain ones.
    text = unicodedata.normalize("NFKC", raw)
    text = _INVISIBLE.sub("", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse spaces and tabs inside each line, and trim each line.
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
    text = "\n".join(lines)

    # Three or more newlines become one blank line (a paragraph break).
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_pasted_text(raw: str) -> str:
    """Normalize text the user pasted and check there is enough of it to analyse."""
    text = normalize_text(raw)
    if not text:
        raise InputError("empty_text", "The text box is empty. Paste the policy text and try again.")
    if len(text) < MIN_CHARS:
        raise InputError(
            "text_too_short",
            f"That text is only {len(text)} characters. Paste the full policy "
            f"(at least {MIN_CHARS} characters).",
        )
    return text
