"""
Settings for PolicyLens, read from environment variables.

Values come from the real environment first, then from server/.env if it exists.
We use a tiny hand-written .env reader instead of the python-dotenv library,
because the format we need (KEY=value lines) is simple and it saves a dependency.
"""

import os
from pathlib import Path

# server/.env sits one folder above this file's folder (server/app/).
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"

# Used when ANTHROPIC_MODEL is blank. We start with the most capable model because
# the rules are strict (exact quotes, word limits). Set ANTHROPIC_MODEL=claude-sonnet-5-5
# for half the price per token, and compare results in Stage 6 before switching.
DEFAULT_MODEL = "claude-opus-5-5"


def load_env_file(path: Path) -> None:
    """Read KEY=value lines from a .env file into os.environ.

    Blank lines and lines starting with # are skipped. Variables that are
    already set in the real environment are never overwritten.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        # Allow KEY="value" or KEY='value' by removing one pair of matching quotes.
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


class Settings:
    """All configuration in one place, so the rest of the code never reads os.environ."""

    def __init__(self) -> None:
        load_env_file(ENV_FILE)

        self.anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self.anthropic_model = os.environ.get("ANTHROPIC_MODEL", "").strip() or DEFAULT_MODEL
        self.port = int(os.environ.get("PORT", "8000"))

        # Fail fast with a clear message instead of a confusing error at the first request.
        if not self.anthropic_api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Copy server/.env.example to server/.env "
                "and add your key."
            )


# One shared settings object, created when the app starts.
settings = Settings()
