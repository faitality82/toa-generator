"""Rule-based reclassification for edge cases.

Catches common misclassifications:
- Treatises incorrectly identified as cases (due to vol+reporter pattern)
- Law review articles misidentified as cases
- Flags low-confidence entries for AI review
"""

from __future__ import annotations

import re

from app.models import Citation, CitationCategory

# Known treatise patterns that might match case regex
TREATISE_SIGNALS = [
    r"Wright\s*[&,]\s*Miller",
    r"Moore['']s\s+Federal\s+Practice",
    r"Prosser\s*[&,]\s*Keeton",
    r"Wigmore",
    r"Corbin\s+on\s+Contracts",
    r"Williston\s+on\s+Contracts",
    r"Am\.?\s*Jur\.?\s*2d",
    r"C\.?J\.?S\.?",
    r"A\.?L\.?R\.?",
]

_TREATISE_RE = re.compile("|".join(TREATISE_SIGNALS), re.IGNORECASE)

# Law review signals
_LAW_REVIEW_RE = re.compile(
    r"(?:L\.?\s*Rev|Law\s+Review|L\.?\s*J|Law\s+Journal)",
    re.IGNORECASE,
)


def reclassify(citations: list[Citation]) -> list[Citation]:
    """Post-process citations to fix common misclassifications.

    Modifies citations in-place and returns the list.
    Also flags low-confidence entries.

    Args:
        citations: List of detected citations to reclassify.

    Returns:
        The same list, modified in place.
    """
    ambiguous: list[Citation] = []

    for cite in citations:
        if cite.is_short_form:
            continue

        text = cite.full_text

        # Check if a "case" is actually a treatise
        if cite.category == CitationCategory.CASES and _TREATISE_RE.search(text):
            cite.category = CitationCategory.OTHER
            cite.confidence = 0.9
            continue

        # Check if a "case" is actually a law review article
        if cite.category == CitationCategory.CASES and _LAW_REVIEW_RE.search(text):
            cite.category = CitationCategory.OTHER
            cite.confidence = 0.9
            continue

        # Flag citations with suspicious patterns
        if cite.category == CitationCategory.CASES:
            # No party names detected (might not be a real case)
            if " v." not in text and " v " not in text:
                if not re.match(r"(?:In\s+re|Ex\s+parte|Matter\s+of)", text):
                    cite.confidence = 0.6
                    ambiguous.append(cite)

    return citations


def get_ambiguous(citations: list[Citation], threshold: float = 0.8) -> list[Citation]:
    """Return citations below the confidence threshold for AI review.

    Args:
        citations: All citations.
        threshold: Confidence threshold (default 0.8).

    Returns:
        List of low-confidence citations.
    """
    return [c for c in citations if c.confidence < threshold and not c.is_short_form]
