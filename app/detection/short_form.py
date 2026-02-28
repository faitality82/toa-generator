"""Resolve short-form citations (Id., supra, short pincite) to their parents.

Short-form resolution rules:
- Id. / Ibid. → resolves to the most recent prior citation (in document order)
- supra → matches first-party name against prior full citations
- Short pincite (e.g., "123 F.3d at 456") → matches vol+reporter to prior cite
"""

from __future__ import annotations

import re

from app.models import Citation


def resolve_short_forms(
    full_cites: list[Citation],
    short_cites: list[Citation],
) -> None:
    """Resolve short-form citations in-place.

    Sets each short cite's parent_key to the normalized_key of its parent.
    Operates on page-order assumption (citations are listed in document order).

    Args:
        full_cites: All full (non-short-form) citations in document order.
        short_cites: All short-form citations to resolve.
    """
    if not full_cites or not short_cites:
        return

    # Build a page-ordered list of full citations for Id. resolution
    ordered_fulls = sorted(full_cites, key=lambda c: (min(c.pages) if c.pages else 0))

    for sc in short_cites:
        sc_page = min(sc.pages) if sc.pages else 0
        text = sc.full_text.strip()

        if _is_id_cite(text):
            _resolve_id(sc, ordered_fulls, sc_page)
        elif _is_supra_cite(text):
            _resolve_supra(sc, ordered_fulls, text)
        else:
            _resolve_short_pincite(sc, full_cites, text)


def _is_id_cite(text: str) -> bool:
    """Check if text is an Id./Ibid. citation."""
    return bool(re.match(r"^Id\.|^Ibid\.", text, re.IGNORECASE))


def _is_supra_cite(text: str) -> bool:
    """Check if text contains 'supra'."""
    return "supra" in text.lower()


def _resolve_id(
    short_cite: Citation,
    ordered_fulls: list[Citation],
    sc_page: int,
) -> None:
    """Resolve Id. to the most recent prior citation.

    The Id. citation refers to the immediately preceding citation in the brief.
    We find the last full citation that appears on the same page or earlier.
    """
    best: Citation | None = None
    for fc in ordered_fulls:
        fc_page = min(fc.pages) if fc.pages else 0
        if fc_page <= sc_page:
            best = fc
        else:
            break

    if best:
        short_cite.parent_key = best.normalized_key
        short_cite.category = best.category


def _resolve_supra(
    short_cite: Citation,
    ordered_fulls: list[Citation],
    text: str,
) -> None:
    """Resolve supra by matching first-party name.

    Format: "Smith, supra, at 123" → find full cite with "Smith" as first party.
    """
    # Extract the name before "supra"
    match = re.match(r"^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", text)
    if not match:
        return
    name = match.group(1).lower()

    for fc in ordered_fulls:
        # Check if the full citation starts with this party name
        fc_first_party = fc.display_name.split(" v.")[0].split(" v ")[0].strip().lower()
        if name in fc_first_party or fc_first_party.startswith(name):
            short_cite.parent_key = fc.normalized_key
            short_cite.category = fc.category
            return


def _resolve_short_pincite(
    short_cite: Citation,
    full_cites: list[Citation],
    text: str,
) -> None:
    """Resolve short pincite by matching volume + reporter.

    Format: "123 F.3d at 456" → find full cite with "123 F.3d".
    """
    match = re.match(r"(\d+)\s+(\S+(?:\.\S+)*)", text)
    if not match:
        return

    vol = match.group(1)
    reporter = re.sub(r"[\s.]", "", match.group(2).lower())

    for fc in full_cites:
        fc_match = re.search(r"(\d+)\s+(\S+(?:\.\S+)*)", fc.full_text)
        if fc_match:
            fc_vol = fc_match.group(1)
            fc_reporter = re.sub(r"[\s.]", "", fc_match.group(2).lower())
            if vol == fc_vol and reporter == fc_reporter:
                short_cite.parent_key = fc.normalized_key
                short_cite.category = fc.category
                return
