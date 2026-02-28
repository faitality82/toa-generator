"""Extract text with page numbers from .pdf files."""

from __future__ import annotations

from pathlib import Path

import pdfplumber

from app.parsers.docx_parser import PageText


def parse_pdf(path: str | Path) -> list[PageText]:
    """Parse a PDF file and return text grouped by page number.

    Uses pdfplumber's native page boundaries — each PDF page maps
    directly to a page number.
    """
    pages: list[PageText] = []

    with pdfplumber.open(str(path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            text = text.strip()
            if text:
                pages.append(PageText(page=i, text=text))

    return pages
