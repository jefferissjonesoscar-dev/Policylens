"""
Tests for PDF text extraction. PDFs are built in memory by pdf_helpers.make_pdf.
"""

import base64
import unittest

from app.errors import InputError
from app.input import pdf as pdf_module
from app.input.pdf import text_from_pdf_base64, text_from_pdf_bytes
from tests.pdf_helpers import make_pdf

POLICY_LINES = [
    "Privacy Policy",
    "We collect your name, email address and device identifiers.",
    "We share your data with analytics providers and advertising partners.",
    "We keep your information for three years after your last login.",
    "You can delete your account at any time from the settings page.",
]


class PdfExtractionTests(unittest.TestCase):
    def test_extracts_text_from_every_page(self):
        text = text_from_pdf_bytes(make_pdf([POLICY_LINES[:3], POLICY_LINES[3:]]))
        for line in POLICY_LINES:
            self.assertIn(line, text)
        # Pages are separated by a paragraph break, so the chunker can split there.
        self.assertIn("advertising partners.\n\nWe keep", text)

    def test_base64_input_is_decoded(self):
        encoded = base64.b64encode(make_pdf([POLICY_LINES])).decode("ascii")
        self.assertIn("three years", text_from_pdf_base64(encoded))

    def assert_rejected(self, func, value, code):
        with self.assertRaises(InputError) as caught:
            func(value)
        self.assertEqual(caught.exception.code, code)

    def test_invalid_base64_is_rejected(self):
        self.assert_rejected(text_from_pdf_base64, "not base64!!", "invalid_pdf")

    def test_non_pdf_file_is_rejected(self):
        self.assert_rejected(text_from_pdf_bytes, b"PK\x03\x04 a zip file", "invalid_pdf")

    def test_damaged_pdf_is_rejected(self):
        with self.assertLogs("pypdf", level="WARNING"):  # pypdf warns about the damage; keep output quiet
            self.assert_rejected(text_from_pdf_bytes, b"%PDF-1.4\nthis is not really a pdf", "invalid_pdf")

    def test_pdf_without_text_is_explained(self):
        # Like a scanned document: valid PDF, but no text layer to read.
        self.assert_rejected(text_from_pdf_bytes, make_pdf([[]]), "pdf_no_text")

    def test_oversized_pdf_is_rejected_before_decoding(self):
        too_big = "A" * (pdf_module.MAX_PDF_BYTES * 4 // 3 + 8)
        self.assert_rejected(text_from_pdf_base64, too_big, "pdf_too_large")


if __name__ == "__main__":
    unittest.main()
