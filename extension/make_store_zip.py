"""
Build the zip file to upload to the Chrome Web Store.

The extension in this folder talks to http://localhost:8000 for development.
The store version must talk to your hosted server instead, so this script
copies the extension files into a zip and swaps in that server address:
  - popup.js: DEFAULT_SERVER becomes your server
  - manifest.json: the extension may only contact your server (no localhost,
    no optional "any website" permission, which would slow down store review)

Usage (from the repository root):
    python extension/make_store_zip.py https://policylens-xxxx.europe-west1.run.app

The zip is written to extension/dist/policylens-extension.zip.
"""

import json
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlparse

EXTENSION_DIR = Path(__file__).resolve().parent
OUTPUT = EXTENSION_DIR / "dist" / "policylens-extension.zip"

# Only these files go into the store package (no README, no this script).
FILES = ["manifest.json", "popup.html", "popup.css", "popup.js", "icon.png"]

DEV_SERVER_LINE = 'const DEFAULT_SERVER = "http://localhost:8000";'


def check_server(url: str) -> str:
    """Return the server's origin (scheme + host), or exit with a clear message."""
    parsed = urlparse(url)
    # The store build must use HTTPS: the policy text a user sends is private.
    if parsed.scheme != "https" or not parsed.netloc:
        sys.exit(f"Server address must start with https://, got: {url}")
    return f"{parsed.scheme}://{parsed.netloc}"


def store_manifest(origin: str) -> str:
    manifest = json.loads((EXTENSION_DIR / "manifest.json").read_text(encoding="utf-8"))
    manifest["host_permissions"] = [f"{origin}/*"]
    manifest.pop("optional_host_permissions", None)
    return json.dumps(manifest, indent=2) + "\n"


def store_popup_js(origin: str) -> str:
    source = (EXTENSION_DIR / "popup.js").read_text(encoding="utf-8")
    # Fail loudly if someone changed that line, rather than shipping localhost.
    if DEV_SERVER_LINE not in source:
        sys.exit(f"Couldn't find this line in popup.js to replace:\n  {DEV_SERVER_LINE}")
    return source.replace(DEV_SERVER_LINE, f'const DEFAULT_SERVER = "{origin}";')


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    origin = check_server(sys.argv[1])

    OUTPUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for name in FILES:
            if name == "manifest.json":
                zip_file.writestr(name, store_manifest(origin))
            elif name == "popup.js":
                zip_file.writestr(name, store_popup_js(origin))
            else:
                zip_file.write(EXTENSION_DIR / name, name)

    print(f"Built {OUTPUT} for server {origin}")


if __name__ == "__main__":
    main()
