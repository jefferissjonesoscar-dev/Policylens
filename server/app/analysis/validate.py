"""
Check Claude's answer against every rule the result must follow.

Each check returns a list of problems written as short sentences. An empty list
means the answer passed. The same sentences are sent back to Claude when we
retry, so they say exactly what to fix.
"""

from app.analysis.prompts import (
    CATEGORIES,
    MAX_BULLET_WORDS,
    MAX_REASON_WORDS,
    NOT_STATED,
    RISK_LEVELS,
)
from app.analysis.quotes import normalize_for_match, quote_in_source


def _word_count(text: str) -> int:
    return len(text.split())


def _short(text: str, limit: int = 80) -> str:
    """Shorten long text for use inside a problem message."""
    return text if len(text) <= limit else text[:limit] + "..."


def validate_summary(data: dict, source_text: str) -> list[str]:
    """Return the list of rule violations in a summary result (empty if it's valid)."""
    problems: list[str] = []
    normalized_source = normalize_for_match(source_text)

    bullets = data.get("bullets")
    if not isinstance(bullets, list):
        return ['"bullets" must be a list.']

    if len(bullets) != len(CATEGORIES):
        problems.append(f"There must be exactly {len(CATEGORIES)} bullets; there were {len(bullets)}.")

    categories = [b.get("category") for b in bullets if isinstance(b, dict)]
    if categories != CATEGORIES:
        problems.append(f"Bullet categories must be, in order: {', '.join(CATEGORIES)}.")

    for number, bullet in enumerate(bullets, start=1):
        if not isinstance(bullet, dict):
            problems.append(f"Bullet {number} must be an object.")
            continue
        text = str(bullet.get("text", "")).strip()
        quote = str(bullet.get("quote", "")).strip()

        if not text:
            problems.append(f"Bullet {number} has no text.")
        elif _word_count(text) > MAX_BULLET_WORDS:
            problems.append(
                f"Bullet {number} has {_word_count(text)} words; the limit is {MAX_BULLET_WORDS}."
            )

        if not quote:
            if NOT_STATED not in text.lower():
                problems.append(
                    f'Bullet {number} has no quote, so its text must say "{NOT_STATED}".'
                )
        elif not quote_in_source(quote, normalized_source):
            problems.append(f'Bullet {number} quote was not found in the document: "{_short(quote)}"')

    if data.get("risk_level") not in RISK_LEVELS:
        problems.append(f'"risk_level" must be one of: {", ".join(RISK_LEVELS)}.')

    reason = str(data.get("risk_reason", "")).strip()
    if not reason:
        problems.append('"risk_reason" is empty.')
    elif _word_count(reason) > MAX_REASON_WORDS:
        problems.append(f'"risk_reason" has {_word_count(reason)} words; the limit is {MAX_REASON_WORDS}.')

    return problems


def keep_verified_findings(findings: list[dict], chunk_text: str) -> list[dict]:
    """From one chunk's findings, keep only well-formed ones whose quote is really in the chunk.

    Findings are an intermediate step, so instead of retrying we simply drop bad ones;
    the merge step still has the findings from every other chunk to choose from.
    """
    normalized_chunk = normalize_for_match(chunk_text)
    kept = []
    for finding in findings:
        text = str(finding.get("text", "")).strip()
        quote = str(finding.get("quote", "")).strip()
        if (
            finding.get("category") in CATEGORIES
            and text
            and _word_count(text) <= MAX_BULLET_WORDS
            and quote_in_source(quote, normalized_chunk)
        ):
            kept.append({"category": finding["category"], "text": text, "quote": quote})
    return kept
