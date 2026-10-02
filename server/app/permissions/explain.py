"""
Find permission names in whatever the user pasted and explain each one.

People paste permissions in different forms: one per line, comma-separated, a
store page's list, or raw AndroidManifest.xml lines such as
<uses-permission android:name="android.permission.CAMERA" />. We pull out
anything that looks like a permission name and ignore the rest.
"""

import re

from app.errors import InputError
from app.permissions.catalog import ANDROID_PREFIX, CATALOG

MAX_PERMISSIONS = 200
MAX_INPUT_CHARS = 50_000  # comfortably fits a whole AndroidManifest.xml permission section

# Words made of letters, digits, dots and underscores (permission names never contain other characters).
_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_.]*")
_IOS_KEY = re.compile(r"^(NS\w+UsageDescription|NFCReaderUsageDescription)$")
_ANDROID_SHORT = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")  # e.g. CAMERA, READ_CONTACTS

RISK_ORDER = {"High": 0, "Medium": 1, "Low": 2}


def find_permission_names(raw: str) -> list[str]:
    """Return the permission names found in the text, in order, without duplicates."""
    names: list[str] = []
    for token in _TOKEN.findall(raw):
        token = token.strip(".")
        if _IOS_KEY.match(token) or ".permission." in token:
            name = token
        elif _ANDROID_SHORT.match(token) and ANDROID_PREFIX + token in CATALOG:
            # A short name like "CAMERA" -> "android.permission.CAMERA". Only names we
            # know are accepted, so capitalised words like "GPS" in pasted text are ignored.
            name = ANDROID_PREFIX + token
        else:
            continue  # ordinary words such as "uses-permission" or "android:name"
        if name not in names:
            names.append(name)
    return names


def explain_permissions(raw: str) -> list[dict]:
    """Explain every permission found in the text, most sensitive first."""
    if len(raw) > MAX_INPUT_CHARS:
        raise InputError("too_long", f"Please paste at most {MAX_INPUT_CHARS:,} characters.")
    names = find_permission_names(raw)
    if not names:
        raise InputError(
            "no_permissions_found",
            "We couldn't find any permission names. Paste names like android.permission.CAMERA "
            "or NSCameraUsageDescription, one per line.",
        )
    if len(names) > MAX_PERMISSIONS:
        raise InputError("too_many_permissions", f"Please paste at most {MAX_PERMISSIONS} permissions at a time.")

    results = []
    for name in names:
        known = CATALOG.get(name)
        if known:
            results.append({"name": name, **known._asdict()})
        else:
            results.append({
                "name": name,
                "platform": "iOS" if name.startswith("NS") else "Android",
                "title": "Not in our list yet",
                "explanation": "We don't have a plain-language explanation for this permission yet. "
                               "Search for its name to learn what it allows.",
                "risk_level": None,
            })

    # Most sensitive first; unknown ones last. sorted() keeps input order within each level.
    return sorted(results, key=lambda p: RISK_ORDER.get(p["risk_level"], len(RISK_ORDER)))
