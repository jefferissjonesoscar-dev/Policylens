"""
Run the full analysis on a real policy and print the result. Uses your API key
from server/.env, so each run is a real (paid) API call.

Run from the server/ folder:
    python -m scripts.try_analysis --url https://example.com/privacy
    python -m scripts.try_analysis --file policy.txt
"""

import argparse
import json
import logging
import sys

from app.analysis.analyze import analyze_policy
from app.errors import AnalysisError, InputError
from app.input.text import clean_pasted_text
from app.input.url import text_from_url


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyse a policy with Claude and print the JSON result.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="a web page to fetch")
    source.add_argument("--file", help="a text file to treat as pasted text")
    args = parser.parse_args()

    # Show the retry and warning messages from the analysis step.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    try:
        if args.url:
            text = text_from_url(args.url)
        else:
            with open(args.file, encoding="utf-8") as f:
                text = clean_pasted_text(f.read())
        result = analyze_policy(text)
    except (InputError, AnalysisError) as error:
        print(f"Error [{error.code}]: {error.message}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
