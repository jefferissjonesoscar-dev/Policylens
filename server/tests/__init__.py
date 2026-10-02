# The app refuses to start without an API key (see app/config.py). The normal
# tests never call the real API, so a placeholder key is enough to load the
# modules. Live tests (POLICYLENS_LIVE_TESTS=1) need the real key from the
# environment or server/.env, so no placeholder is set for them.
import os

if os.environ.get("POLICYLENS_LIVE_TESTS") != "1":
    os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used")
