"""
Turn policy text into the final result:

    {"bullets": [{"text", "category", "quote"} x5], "risk_level", "risk_reason"}

Short documents (one chunk) take a single Claude call. Long documents use two
steps: pull findings out of each chunk in parallel, then merge them into the
final 5 bullets.

Every final answer is checked by validate.py. If it fails, we ask once more with
the list of problems; if the second answer also fails, we return an error rather
than show the user something unverified.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor

from app.analysis import prompts
from app.analysis.claude_client import InvalidReplyError, ask_claude_for_json
from app.analysis.validate import keep_verified_findings, validate_summary
from app.errors import AnalysisError
from app.input.chunk import split_into_chunks

logger = logging.getLogger(__name__)

# How many chunks are analysed at the same time. Kept small to stay well
# inside API rate limits.
MAX_PARALLEL_CHUNKS = 4


def analyze_policy(text: str) -> dict:
    """Analyse cleaned policy text and return the validated result."""
    chunks = split_into_chunks(text)
    if len(chunks) == 1:
        system, body = prompts.SUMMARY_PROMPT, prompts.wrap_document(text)
    else:
        findings = _collect_findings(chunks)
        findings_json = json.dumps(findings, ensure_ascii=False, indent=1)
        system, body = prompts.MERGE_PROMPT, prompts.wrap_findings(findings_json)

    # Quotes are always checked against the full document, whichever path ran.
    return _summarize_with_one_retry(system, body, source_text=text)


def _summarize_with_one_retry(system: str, body: str, source_text: str) -> dict:
    """Ask for the summary, check it, and retry once with the problems listed if it fails."""
    message = body
    for attempt in (1, 2):
        try:
            result = ask_claude_for_json(system, message, prompts.SUMMARY_SCHEMA)
            problems = validate_summary(result, source_text)
        except InvalidReplyError as error:
            problems = [str(error)]

        if not problems:
            return _clean(result)

        logger.warning("Attempt %d failed checks: %s", attempt, problems)
        message = body + "\n\n" + prompts.retry_note(problems)

    raise AnalysisError(
        "analysis_failed_checks",
        "We couldn't produce a summary with verified quotes for this document. Please try again.",
    )


def _collect_findings(chunks: list[str]) -> list[dict]:
    """Get verified findings from every chunk, analysing several chunks at once."""

    def findings_for(chunk: str) -> list[dict]:
        message = prompts.wrap_document(chunk)
        try:
            reply = ask_claude_for_json(prompts.FINDINGS_PROMPT, message, prompts.FINDINGS_SCHEMA)
        except InvalidReplyError:
            # One unreadable chunk shouldn't sink the whole analysis; the merge
            # step works with whatever the other chunks found.
            logger.warning("Skipping a chunk whose reply was not valid JSON")
            return []
        return keep_verified_findings(reply.get("findings", []), chunk)

    with ThreadPoolExecutor(max_workers=MAX_PARALLEL_CHUNKS) as pool:
        per_chunk = list(pool.map(findings_for, chunks))

    all_findings = [finding for findings in per_chunk for finding in findings]
    if not all_findings:
        raise AnalysisError(
            "no_findings",
            "We couldn't find privacy or terms information in this document. Is it the right text?",
        )
    return all_findings


def _clean(result: dict) -> dict:
    """Return only the fields in our output contract, with surrounding spaces trimmed."""
    return {
        "bullets": [
            {
                "text": bullet["text"].strip(),
                "category": bullet["category"],
                "quote": bullet["quote"].strip(),
            }
            for bullet in result["bullets"]
        ],
        "risk_level": result["risk_level"],
        "risk_reason": result["risk_reason"].strip(),
    }
