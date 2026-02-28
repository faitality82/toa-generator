"""Data models for the TOA Generator."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class CitationCategory(str, Enum):
    """Standard TOA citation categories in display order."""

    CASES = "Cases"
    STATUTES = "Statutes"
    CONSTITUTIONAL = "Constitutional Provisions"
    RULES = "Rules"
    OTHER = "Other Authorities"

    @property
    def sort_order(self) -> int:
        return list(CitationCategory).index(self)


@dataclass
class Citation:
    """A single legal citation extracted from the brief."""

    full_text: str  # Raw text as found in document
    display_name: str  # Formatted name for TOA (e.g., italic case name)
    category: CitationCategory
    pages: list[int] = field(default_factory=list)  # Page numbers where cited
    is_primary: bool = False  # Asterisk (*) in TOA
    is_short_form: bool = False  # Id., supra, short pincite
    parent_key: Optional[str] = None  # Normalized key of parent (for short forms)
    normalized_key: str = ""  # Dedup key (e.g., "123_f3d_456")
    confidence: float = 1.0  # Detection confidence (0.0–1.0)
    sort_key: str = ""  # For ordering within category

    @property
    def page_display(self) -> str:
        """Format page numbers for TOA display (e.g., '1, 3, 5-7')."""
        if not self.pages:
            return ""
        pages = sorted(set(self.pages))
        ranges = []
        start = pages[0]
        end = pages[0]
        for p in pages[1:]:
            if p == end + 1:
                end = p
            else:
                ranges.append(f"{start}" if start == end else f"{start}-{end}")
                start = end = p
        ranges.append(f"{start}" if start == end else f"{start}-{end}")
        return ", ".join(ranges)

    def generate_sort_key(self) -> str:
        """Generate alphabetical sort key from display name."""
        # Strip leading articles and punctuation for sorting
        name = self.display_name.strip()
        # Remove leading * for primary authorities
        name = name.lstrip("*").strip()
        # Remove leading articles
        for article in ("A ", "An ", "The "):
            if name.startswith(article):
                name = name[len(article):]
                break
        # Remove non-alphanumeric for clean sorting
        self.sort_key = re.sub(r"[^a-z0-9 ]", "", name.lower()).strip()
        return self.sort_key

    def merge_pages(self, other: Citation) -> None:
        """Merge page numbers from another citation of the same authority."""
        for p in other.pages:
            if p not in self.pages:
                self.pages.append(p)
        self.pages.sort()


@dataclass
class CourtPreset:
    """Court-specific TOA formatting rules."""

    name: str  # Display name (e.g., "Michigan Court of Appeals")
    code: str  # Short code (e.g., "michigan_coa")
    categories_order: list[CitationCategory] = field(
        default_factory=lambda: list(CitationCategory)
    )
    case_italics: bool = True  # Italicize case names
    primary_marker: str = "*"  # Marker for primary authorities
    font_name: str = "Times New Roman"
    font_size_title: int = 14
    font_size_heading: int = 12
    font_size_body: int = 12
    hanging_indent_inches: float = 0.5
    tab_position_inches: float = 6.5
    notes: str = ""  # Court rule reference (e.g., "MCR 7.212(D)")


@dataclass
class TOAProject:
    """Holds the state for a single TOA generation session."""

    source_path: Optional[str] = None
    source_type: Optional[str] = None  # "docx" or "pdf"
    citations: list[Citation] = field(default_factory=list)
    preset: Optional[CourtPreset] = None
    output_path: Optional[str] = None

    @property
    def primary_citations(self) -> list[Citation]:
        return [c for c in self.citations if not c.is_short_form]

    @property
    def citation_count(self) -> int:
        return len(self.primary_citations)

    def citations_by_category(self) -> dict[CitationCategory, list[Citation]]:
        """Group non-short-form citations by category, sorted."""
        grouped: dict[CitationCategory, list[Citation]] = {}
        for cat in CitationCategory:
            entries = [
                c for c in self.citations
                if c.category == cat and not c.is_short_form
            ]
            if entries:
                for e in entries:
                    if not e.sort_key:
                        e.generate_sort_key()
                entries.sort(key=lambda c: c.sort_key)
                grouped[cat] = entries
        return grouped
