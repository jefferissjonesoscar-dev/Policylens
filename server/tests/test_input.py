"""
Tests for Stage 2 input handling. Uses Python's built-in unittest, so no extra library.

Run from the server/ folder:
    python -m unittest discover -s tests -v

These tests don't touch the network: URL tests only check the address
validation, which rejects bad addresses before any download.
"""

import unittest

from app.errors import InputError
from app.input.chunk import split_into_chunks
from app.input.html_extract import extract_main_text
from app.input.text import MIN_CHARS, clean_pasted_text, normalize_text
from app.input.url import check_url_is_public


class NormalizeTextTests(unittest.TestCase):
    def test_collapses_spaces_and_blank_lines(self):
        raw = "We   collect\tdata.\r\n\r\n\r\n\r\nWe share it."
        self.assertEqual(normalize_text(raw), "We collect data.\n\nWe share it.")

    def test_removes_invisible_characters_and_non_breaking_spaces(self):
        raw = "We sell​ your data."
        self.assertEqual(normalize_text(raw), "We sell your data.")


class CleanPastedTextTests(unittest.TestCase):
    def test_empty_text_is_rejected(self):
        with self.assertRaises(InputError) as caught:
            clean_pasted_text("   \n  ")
        self.assertEqual(caught.exception.code, "empty_text")

    def test_short_text_is_rejected(self):
        with self.assertRaises(InputError) as caught:
            clean_pasted_text("We collect your email.")
        self.assertEqual(caught.exception.code, "text_too_short")

    def test_valid_text_is_returned_clean(self):
        text = "We collect your email address. " * 10
        self.assertEqual(clean_pasted_text(text), text.strip())
        self.assertGreaterEqual(len(clean_pasted_text(text)), MIN_CHARS)


class ExtractMainTextTests(unittest.TestCase):
    POLICY = "We collect your name and email address when you sign up. " * 12

    def test_drops_scripts_navigation_and_footer(self):
        html = f"""
        <html><head><title>Privacy</title><style>p {{ color: red; }}</style></head>
        <body>
          <nav><a href="/">Home</a> <a href="/shop">Shop</a></nav>
          <div role="navigation">Menu</div>
          <p>{self.POLICY}</p>
          <script>trackUser();</script>
          <footer>Copyright 2026</footer>
        </body></html>
        """
        text = extract_main_text(html)
        self.assertIn("We collect your name", text)
        for unwanted in ("Home", "Shop", "Menu", "trackUser", "color: red", "Copyright"):
            self.assertNotIn(unwanted, text)

    def test_prefers_main_element_when_present(self):
        html = f"<body><div>Sign up for our newsletter!</div><main><p>{self.POLICY}</p></main></body>"
        text = extract_main_text(html)
        self.assertIn("We collect your name", text)
        self.assertNotIn("newsletter", text)

    def test_falls_back_to_whole_page_when_main_is_tiny(self):
        html = f"<body><main>Skip to content</main><p>{self.POLICY}</p></body>"
        self.assertIn("We collect your name", extract_main_text(html))

    def test_nested_skipped_tags_end_at_the_matching_close_tag(self):
        html = "<nav><nav>inner</nav>still nav</nav><p>Visible text.</p>"
        self.assertEqual(extract_main_text(html), "Visible text.")

    def test_blocks_become_paragraphs_and_table_cells_stay_on_one_line(self):
        html = "<h2>Data we collect</h2><p>Email.</p><table><tr><td>Name</td><td>Kept 2 years</td></tr></table>"
        self.assertEqual(extract_main_text(html), "Data we collect\n\nEmail.\n\nName Kept 2 years")

    def test_decodes_html_entities(self):
        self.assertEqual(extract_main_text("<p>Terms &amp; Conditions</p>"), "Terms & Conditions")


class SplitIntoChunksTests(unittest.TestCase):
    def test_short_text_is_one_chunk(self):
        self.assertEqual(split_into_chunks("Short policy.", max_chars=100), ["Short policy."])

    def test_long_text_is_split_on_paragraphs_within_the_limit(self):
        paragraphs = [f"Paragraph {i}. " + "word " * 30 for i in range(40)]
        text = "\n\n".join(p.strip() for p in paragraphs)
        chunks = split_into_chunks(text, max_chars=1_000, overlap_chars=0)

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 1_000)
        # With no overlap, the chunks rejoin into exactly the original text.
        self.assertEqual("\n\n".join(chunks), text)

    def test_overlap_repeats_the_previous_paragraph(self):
        text = "\n\n".join(["A" * 400, "B" * 400, "C" * 400])
        chunks = split_into_chunks(text, max_chars=850, overlap_chars=500)
        self.assertEqual(chunks, ["A" * 400 + "\n\n" + "B" * 400, "B" * 400 + "\n\n" + "C" * 400])

    def test_giant_paragraph_is_split_by_sentence(self):
        text = "This is one sentence about data. " * 100  # ~3,300 chars, no paragraph breaks
        chunks = split_into_chunks(text.strip(), max_chars=1_000)
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 1_000)
            self.assertTrue(chunk.endswith("."), "chunks should end at a sentence boundary")


class CheckUrlIsPublicTests(unittest.TestCase):
    def assert_rejected(self, url, code):
        with self.assertRaises(InputError) as caught:
            check_url_is_public(url)
        self.assertEqual(caught.exception.code, code)

    def test_rejects_non_web_schemes(self):
        self.assert_rejected("file:///etc/passwd", "invalid_url")
        self.assert_rejected("ftp://example.com/policy.txt", "invalid_url")

    def test_rejects_missing_host(self):
        self.assert_rejected("https://", "invalid_url")

    def test_rejects_private_and_local_addresses(self):
        for url in (
            "http://localhost/admin",
            "http://127.0.0.1:8000/api/health",
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata service
            "http://[::1]/",
        ):
            with self.subTest(url=url):
                self.assert_rejected(url, "url_not_allowed")


if __name__ == "__main__":
    unittest.main()
