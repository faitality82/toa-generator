"""Citation detection orchestrator.

Pipeline: scan pages → prevent overlaps → normalize → deduplicate →
resolve short forms → merge page numbers → sort.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import Citation, CitationCategory
from app.parsers.docx_parser import PageText
from app.detection.patterns import PATTERN_REGISTRY
from app.detection.short_form import resolve_short_forms


@dataclass
class _RawMatch:
    """Intermediate match before dedup."""

    text: str
    start: int  # Absolute character offset (for overlap detection)
    end: int
    page: int
    pattern_name: str
    category: CitationCategory


class CitationDetector:
    """Detects and organizes legal citations from parsed document pages."""

    def detect(self, pages: list[PageText]) -> list[Citation]:
        """Run the full detection pipeline.

        Args:
            pages: Parsed document pages with text and page numbers.

        Returns:
            Deduplicated, merged list of Citation objects.
        """
        # Step 1: Scan all pages against all patterns
        raw_matches = self._scan(pages)

        # Step 2: Remove overlapping matches (prefer longer/earlier)
        raw_matches = self._remove_overlaps(raw_matches)

        # Step 3: Convert to Citation objects with normalization
        citations = self._to_citations(raw_matches)

        # Step 4: Separate short forms from full citations
        full_cites = [c for c in citations if not c.is_short_form]
        short_cites = [c for c in citations if c.is_short_form]

        # Step 5: Resolve short forms to their parent citations
        resolve_short_forms(full_cites, short_cites)

        # Step 6: Merge pages from short forms into parent citations
        key_to_cite: dict[str, Citation] = {}
        for c in full_cites:
            if c.normalized_key in key_to_cite:
                key_to_cite[c.normalized_key].merge_pages(c)
            else:
                key_to_cite[c.normalized_key] = c

        # Merge short form pages into their parents
        for sc in short_cites:
            if sc.parent_key and sc.parent_key in key_to_cite:
                for p in sc.pages:
                    if p not in key_to_cite[sc.parent_key].pages:
                        key_to_cite[sc.parent_key].pages.append(p)
                        key_to_cite[sc.parent_key].pages.sort()

        # Step 7: Deduplicated list
        result = list(key_to_cite.values())

        # Step 8: Generate sort keys and sort
        for c in result:
            c.generate_sort_key()

        result.sort(key=lambda c: (c.category.sort_order, c.sort_key))

        return result

    def _scan(self, pages: list[PageText]) -> list[_RawMatch]:
        """Scan all pages against all patterns."""
        matches: list[_RawMatch] = []
        char_offset = 0

        for page_data in pages:
            text = page_data.text
            for name, pattern, category in PATTERN_REGISTRY:
                for m in pattern.finditer(text):
                    matches.append(
                        _RawMatch(
                            text=m.group(0).strip(),
                            start=char_offset + m.start(),
                            end=char_offset + m.end(),
                            page=page_data.page,
                            pattern_name=name,
                            category=category,
                        )
                    )
            char_offset += len(text)

        return matches

    def _remove_overlaps(self, matches: list[_RawMatch]) -> list[_RawMatch]:
        """Remove overlapping matches, preferring longer matches first."""
        if not matches:
            return []

        # Sort by length descending, then by start position
        matches.sort(key=lambda m: (-(m.end - m.start), m.start))

        kept: list[_RawMatch] = []
        occupied: list[tuple[int, int]] = []

        for m in matches:
            overlaps = any(
                m.start < occ_end and m.end > occ_start
                for occ_start, occ_end in occupied
            )
            if not overlaps:
                kept.append(m)
                occupied.append((m.start, m.end))

        # Restore original order (by position)
        kept.sort(key=lambda m: m.start)
        return kept

    def _to_citations(self, matches: list[_RawMatch]) -> list[Citation]:
        """Convert raw matches to Citation objects."""
        citations: list[Citation] = []

        for m in matches:
            is_short = m.pattern_name.startswith("short_")
            norm_key = self._normalize(m.text, m.pattern_name) if not is_short else ""
            display = self._make_display_name(m.text, m.category)

            citations.append(
                Citation(
                    full_text=m.text,
                    display_name=display,
                    category=m.category,
                    pages=[m.page],
                    is_short_form=is_short,
                    normalized_key=norm_key,
                    confidence=1.0,
                )
            )

        return citations

    def _normalize(self, text: str, pattern_name: str) -> str:
        """Create a deduplication key from citation text.

        Strips whitespace variations, normalizes reporter names,
        and extracts the core volume-reporter-page triple.
        """
        # Collapse whitespace
        norm = re.sub(r"\s+", " ", text.strip().lower())

        # For cases, extract volume + reporter + start page
        if pattern_name.startswith("case_"):
            vol_match = re.search(r"(\d+)\s+(\S+(?:\.\s*\S+)*)\s+(\d+)", norm)
            if vol_match:
                vol = vol_match.group(1)
                rep = re.sub(r"[\s.]", "", vol_match.group(2))
                page = vol_match.group(3)
                return f"{vol}_{rep}_{page}"

        # For statutes, normalize section numbers
        if pattern_name.startswith("statute_"):
            # Remove § symbols and extra spaces
            norm = re.sub(r"[§]+", "s", norm)
            norm = re.sub(r"[\s.]+", "_", norm)
            return norm

        # For rules, normalize
        if pattern_name.startswith("rule_"):
            norm = re.sub(r"[\s.]+", "_", norm)
            return norm

        # For constitutional provisions
        if pattern_name.startswith("const_"):
            norm = re.sub(r"[\s.]+", "_", norm)
            return norm

        # Fallback: hash the normalized text
        return re.sub(r"[\s.]+", "_", norm)

    def _make_display_name(self, text: str, category: CitationCategory) -> str:
        """Create the display name for the TOA entry."""
        # Clean up whitespace
        display = re.sub(r"\s+", " ", text.strip())

        # For cases, the display name is the full citation as-is
        # (italicization is handled at render time)
        return display
