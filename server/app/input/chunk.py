"""
Split long documents into chunks for analysis.

Most policies fit in a single chunk and are analysed in one call. Very long
documents (for example a terms of service bundled with several annexes) are
split so each request stays a manageable size and each part of the document
gets the model's full attention. Stage 3 analyses each chunk and then merges
the findings into the final 5 bullets.

Chunks break between paragraphs where possible, so a sentence is never cut in
half unless a single sentence is longer than a whole chunk.
"""

import re

# About 10,000 tokens of English text. Well within Claude's limits, while
# keeping each call reasonably fast.
MAX_CHUNK_CHARS = 40_000

# The last paragraph of one chunk is repeated at the start of the next if it is
# at most this long, so a point that spans the boundary isn't lost.
OVERLAP_CHARS = 1_000

PARAGRAPH_BREAK = "\n\n"

# A sentence ends at . ! or ? followed by whitespace.
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def _split_long_paragraph(paragraph: str, max_chars: int) -> list[str]:
    """Split one paragraph that is too long for a chunk into sentence-aligned pieces."""
    pieces: list[str] = []
    current = ""
    for sentence in _SENTENCE_END.split(paragraph):
        # A single "sentence" longer than a chunk (e.g. a giant list with no full stops): hard cut.
        while len(sentence) > max_chars:
            if current:
                pieces.append(current)
                current = ""
            pieces.append(sentence[:max_chars])
            sentence = sentence[max_chars:]

        if current and len(current) + 1 + len(sentence) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}" if current else sentence
    if current:
        pieces.append(current)
    return pieces


def split_into_chunks(
    text: str,
    max_chars: int = MAX_CHUNK_CHARS,
    overlap_chars: int = OVERLAP_CHARS,
) -> list[str]:
    """Return the text as a list of chunks, each at most max_chars long."""
    if len(text) <= max_chars:
        return [text]

    # Break into paragraphs, splitting any paragraph that alone is too big.
    paragraphs: list[str] = []
    for paragraph in text.split(PARAGRAPH_BREAK):
        if len(paragraph) > max_chars:
            paragraphs.extend(_split_long_paragraph(paragraph, max_chars))
        else:
            paragraphs.append(paragraph)

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        added_len = len(paragraph) + (len(PARAGRAPH_BREAK) if current else 0)

        if current and current_len + added_len > max_chars:
            chunks.append(PARAGRAPH_BREAK.join(current))

            # Start the next chunk with the previous paragraph as overlap,
            # but only if it is short and still leaves room for this paragraph.
            last = current[-1]
            if len(last) <= overlap_chars and len(last) + len(PARAGRAPH_BREAK) + len(paragraph) <= max_chars:
                current, current_len = [last], len(last)
            else:
                current, current_len = [], 0
            added_len = len(paragraph) + (len(PARAGRAPH_BREAK) if current else 0)

        current.append(paragraph)
        current_len += added_len

    if current:
        chunks.append(PARAGRAPH_BREAK.join(current))
    return chunks
