"""
Build small, valid PDF files in memory for tests, so we don't need to commit
binary files or install a PDF-writing library.

The PDF has one page per entry in `pages`, each showing its lines of text in
Helvetica. That's enough for pypdf to extract the text back out.
"""


def _escape(text: str) -> str:
    """Escape the characters that are special inside a PDF text string."""
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages: list[list[str]]) -> bytes:
    objects: list[bytes] = []

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)  # PDF object numbers start at 1

    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    pages_id = len(objects) + 2 + 2 * len(pages)  # reserved: placed after all page objects
    page_ids = []
    for lines in pages:
        # Text drawn from the top of the page, 14 points per line.
        commands = ["BT", "/F1 11 Tf", "14 TL", "50 780 Td"]
        for line in lines:
            commands.append(f"({_escape(line)}) Tj T*")
        commands.append("ET")
        stream = "\n".join(commands).encode("latin-1")
        content = add(b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream")
        page_ids.append(add(
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>" % (pages_id, font, content)
        ))
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_id)
    kids = b" ".join(b"%d 0 R" % pid for pid in page_ids)
    assert add(b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kids, len(page_ids))) == pages_id

    # Write the objects, remembering where each starts for the cross-reference table.
    output = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(output))
        output += b"%d 0 obj\n" % number + body + b"\nendobj\n"
    xref_start = len(output)
    output += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objects) + 1)
    for offset in offsets:
        output += b"%010d 00000 n \n" % offset
    output += b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objects) + 1, catalog, xref_start)
    return bytes(output)
