"""
Try the Stage 2 input handling by hand and see what text the analyser will get.

Run from the server/ folder:
    python -m scripts.try_input --url https://example.com/privacy
    python -m scripts.try_input --file policy.txt

Prints the text length, how many chunks it splits into, and the start of the text.
"""

import argparse
import sys

from app.errors import InputError
from app.input.chunk import split_into_chunks
from app.input.text import clean_pasted_text
from app.input.url import text_from_url

PREVIEW_CHARS = 800


def main() -> int:
    parser = argparse.ArgumentParser(description="Show the text PolicyLens extracts from an input.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="a web page to fetch")
    source.add_argument("--file", help="a text file to treat as pasted text")
    args = parser.parse_args()

    try:
        if args.url:
            text = text_from_url(args.url)
        else:
            with open(args.file, encoding="utf-8") as f:
                text = clean_pasted_text(f.read())
    except InputError as error:
        print(f"Error [{error.code}]: {error.message}", file=sys.stderr)
        return 1

    chunks = split_into_chunks(text)
    print(f"Characters: {len(text):,}")
    print(f"Chunks:     {len(chunks)} ({', '.join(f'{len(c):,}' for c in chunks)} characters)")
    print("-" * 60)
    print(text[:PREVIEW_CHARS])
    if len(text) > PREVIEW_CHARS:
        print(f"... [{len(text) - PREVIEW_CHARS:,} more characters]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
