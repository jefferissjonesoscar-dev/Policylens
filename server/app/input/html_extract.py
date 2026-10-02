"""
Pull the readable text out of a web page's HTML.

Uses Python's built-in html.parser, so no extra library is needed. The approach:
  1. Drop everything inside tags that never hold policy text (scripts, styles,
     navigation, headers, footers, sidebars, forms).
  2. Turn block-level tags (paragraphs, headings, list items...) into line breaks
     so the text keeps its paragraph structure.
  3. If the page marks its main content with <main> or <article>, prefer that.

This is a heuristic. It works well on the typical policy page, which is mostly
paragraphs and headings, but it can't match a dedicated extraction library on
unusual layouts or pages that build their content with JavaScript.
"""

from html.parser import HTMLParser

from app.input.text import normalize_text

# Tags whose entire contents are skipped.
SKIP_TAGS = {
    "script", "style", "noscript", "template", "svg", "iframe", "canvas",
    "nav", "header", "footer", "aside", "form", "button", "select", "dialog",
}

# ARIA roles that mark the same kinds of page furniture on generic <div>s.
SKIP_ROLES = {"navigation", "banner", "contentinfo", "complementary", "search", "dialog"}

# Tags that start a new line of text.
BLOCK_TAGS = {
    "p", "div", "section", "article", "main", "br", "hr", "li", "ul", "ol",
    "dl", "dt", "dd", "h1", "h2", "h3", "h4", "h5", "h6", "table", "tr",
    "blockquote", "pre", "address", "figcaption",
}

# Table cells: separated by a space so neighbouring cells don't run together.
CELL_TAGS = {"td", "th"}

# Tags that contain the page's main content, when the site uses them.
MAIN_TAGS = {"main", "article"}

# Tags that never have a closing tag, so they must not change any depth counters.
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "source", "track", "wbr",
}

# Use the <main>/<article> text only if it has at least this many characters;
# otherwise the tag probably wrapped something small and we use the whole page.
MIN_MAIN_CHARS = 500


class _TextCollector(HTMLParser):
    """Walks the HTML once, collecting visible text for the whole page and for main content."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)  # turns &amp; etc. into real characters
        self.all_parts: list[str] = []
        self.main_parts: list[str] = []
        self.main_depth = 0  # > 0 while inside <main> or <article>
        # While skipping, remember which tag started it and how deeply that same tag
        # is nested, so the skip ends at its matching close tag and not an inner one.
        self.skip_tag: str | None = None
        self.skip_depth = 0

    def _add(self, piece: str) -> None:
        self.all_parts.append(piece)
        if self.main_depth > 0:
            self.main_parts.append(piece)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self.skip_tag is not None:
            if tag == self.skip_tag:
                self.skip_depth += 1
            return

        if tag in VOID_TAGS:
            if tag in BLOCK_TAGS:  # <br> and <hr>
                self._add("\n")
            return

        role = (dict(attrs).get("role") or "").lower()
        if tag in SKIP_TAGS or role in SKIP_ROLES:
            self.skip_tag = tag
            self.skip_depth = 1
            return

        if tag in MAIN_TAGS:
            self.main_depth += 1
        if tag in BLOCK_TAGS:
            self._add("\n")
        elif tag in CELL_TAGS:
            self._add(" ")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_tag is not None:
            if tag == self.skip_tag:
                self.skip_depth -= 1
                if self.skip_depth == 0:
                    self.skip_tag = None
            return

        if tag in BLOCK_TAGS:
            self._add("\n")
        elif tag in CELL_TAGS:
            self._add(" ")
        if tag in MAIN_TAGS and self.main_depth > 0:
            self.main_depth -= 1

    def handle_data(self, data: str) -> None:
        if self.skip_tag is None:
            self._add(data)


def extract_main_text(html: str) -> str:
    """Return the readable text of an HTML page, with paragraph breaks kept."""
    collector = _TextCollector()
    collector.feed(html)
    collector.close()

    main_text = normalize_text("".join(collector.main_parts))
    if len(main_text) >= MIN_MAIN_CHARS:
        return main_text
    return normalize_text("".join(collector.all_parts))
