"""
Extract text from a PDF using the pypdf library.

pypdf reads the text layer of a PDF. Scanned documents (photos of pages) have
no text layer, so they come back empty; for those we ask the user to paste the
text instead, because recognising text in images (OCR) needs much heavier tools.

PDF text often has line breaks in the middle of sentences, where the page
wrapped. That's fine for analysis, and quote checking ignores line breaks.
"""

import base64
import binascii
import io

from pypdf import PdfReader
from pypdf.errors import DependencyError, PdfReadError

from app.errors import InputError
from app.input.text import MIN_CHARS, normalize_text

MAX_PDF_BYTES = 10 * 1024 * 1024  # 10 MB, matching the limit the frontend shows
MAX_PDF_PAGES = 300  # far beyond any normal policy; stops huge documents tying up the server


def text_from_pdf_base64(encoded: str) -> str:
    """Decode a base64 PDF sent by the frontend and return its text."""
    # Base64 is 4 characters for every 3 bytes, so check the size before decoding.
    if len(encoded) > MAX_PDF_BYTES * 4 // 3 + 4:
        raise InputError("pdf_too_large", "That PDF is larger than 10 MB.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise InputError("invalid_pdf", "That file couldn't be read as a PDF.")
    return text_from_pdf_bytes(data)


def text_from_pdf_bytes(data: bytes) -> str:
    """Return the text of a PDF file's pages, with a blank line between pages."""
    if len(data) > MAX_PDF_BYTES:
        raise InputError("pdf_too_large", "That PDF is larger than 10 MB.")
    if not data.startswith(b"%PDF-"):
        raise InputError("invalid_pdf", "That file isn't a PDF.")

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            # Many PDFs are "encrypted" only to block editing, with an empty open
            # password. Try that; a PDF that needs a real password can't be read.
            if not reader.decrypt(""):
                raise InputError("pdf_encrypted", "That PDF is password-protected. Copy the text and paste it instead.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise InputError("pdf_too_many_pages", f"That PDF has more than {MAX_PDF_PAGES} pages.")
        pages = [page.extract_text() or "" for page in reader.pages]
    except DependencyError:
        # Some encryption types need an extra library (cryptography) we don't install.
        raise InputError("pdf_encrypted", "That PDF is protected in a way we can't open. Copy the text and paste it instead.")
    except PdfReadError:
        raise InputError("invalid_pdf", "That PDF seems to be damaged and couldn't be read.")

    text = normalize_text("\n\n".join(pages))
    if len(text) < MIN_CHARS:
        raise InputError(
            "pdf_no_text",
            "We couldn't find text in that PDF. It may be a scanned image. Copy the text and paste it instead.",
        )
    return text
