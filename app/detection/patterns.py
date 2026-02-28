"""Regex patterns for legal citation detection.

Covers: cases (full, parallel, unpublished), statutes (USC, MCL, public law),
constitutional provisions, court rules, short forms (Id., supra, short pincite),
and other authorities (restatements, law reviews, treatises).
"""

from __future__ import annotations

import re
from app.models import CitationCategory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reporter_alts(*reporters: str) -> str:
    """Build a regex alternation from reporter abbreviations, escaping dots."""
    escaped = [re.escape(r) for r in reporters]
    return "(?:" + "|".join(escaped) + ")"


# ---------------------------------------------------------------------------
# Reporter lists
# ---------------------------------------------------------------------------

FEDERAL_REPORTERS = [
    "U.S.", "S. Ct.", "S.Ct.", "L. Ed.", "L.Ed.", "L. Ed. 2d", "L.Ed.2d",
    "F.", "F.2d", "F.3d", "F.4th",
    "F. Supp.", "F.Supp.", "F. Supp. 2d", "F.Supp.2d",
    "F. Supp. 3d", "F.Supp.3d",
    "F. App'x", "F.App'x", "Fed. Appx.", "Fed.Appx.",
    "B.R.",
]

MICHIGAN_REPORTERS = [
    "Mich", "Mich.", "Mich App", "Mich. App.",
    "NW2d", "N.W.2d", "NW 2d", "N.W. 2d",
    "Mich Ct Cl", "Mich. Ct. Cl.",
]

REGIONAL_REPORTERS = [
    "N.E.2d", "N.E.3d", "N.W.2d", "S.E.2d", "S.W.2d", "S.W.3d",
    "So. 2d", "So.2d", "So. 3d", "So.3d",
    "A.2d", "A.3d", "P.2d", "P.3d",
    "Cal. Rptr.", "Cal.Rptr.", "Cal. Rptr. 2d", "Cal.Rptr.2d",
    "Cal. Rptr. 3d", "Cal.Rptr.3d",
]

ALL_REPORTERS = FEDERAL_REPORTERS + MICHIGAN_REPORTERS + REGIONAL_REPORTERS

_ALL_REPORTERS_RE = _reporter_alts(*ALL_REPORTERS)

# ---------------------------------------------------------------------------
# Case patterns
# ---------------------------------------------------------------------------

# Party name: captures "Name v. Name" or "In re Name" or "Ex parte Name"
_PARTY = (
    r"(?:"
    r"(?:In\s+re|Ex\s+parte|Matter\s+of)\s+[A-Z][A-Za-z\s.''\-]+"
    r"|"
    r"[A-Z][A-Za-z.''\-]+(?:\s+[A-Za-z.''\-]+){0,5}"
    r"\s+v\.?\s+"
    r"[A-Z][A-Za-z.''\-]+(?:\s+[A-Za-z.''\-]+){0,5}"
    r")"
)

# Volume + reporter + page (core cite)
_VOL_REP_PAGE = rf"\d{{1,4}}\s+{_ALL_REPORTERS_RE}\s+\d{{1,5}}"

# Optional pincite: , 123 or at 123
_PINCITE = r"(?:(?:,\s*|\s+at\s+)\d{1,5}(?:[–\-]\d{1,5})?)?"

# Full case: Party, volume reporter page (year)
CASE_FULL = rf"(?:{_PARTY},\s*{_VOL_REP_PAGE}{_PINCITE}(?:\s*\([^)]+\d{{4}}\))?)"

# Parallel citation (Michigan style): vol Rep page; vol Rep page
CASE_PARALLEL = (
    rf"(?:{_PARTY},\s*{_VOL_REP_PAGE}"
    rf"(?:\s*;\s*{_VOL_REP_PAGE})+"
    rf"{_PINCITE}(?:\s*\([^)]+\d{{4}}\))?)"
)

# Unpublished: Party, No. XX-XXXXX, year WL/LEXIS number
CASE_UNPUBLISHED = (
    rf"(?:{_PARTY},\s*"
    r"(?:No\.|Nos\.)\s*[\w\-]+(?:\s*,\s*[\w\-]+)*"
    r",?\s*\d{4}\s+(?:WL|LEXIS)\s+\d+"
    r"(?:\s*\([^)]+\d{4}\))?)"
)

# ---------------------------------------------------------------------------
# Statute patterns
# ---------------------------------------------------------------------------

# Federal statutes: 42 U.S.C. § 1983 or 28 USC § 1291(a)(1)
STATUTE_USC = (
    r"(?:\d{1,2}\s+U\.?\s*S\.?\s*C\.?(?:\.?A\.?)?\s*"
    r"§+\s*[\d]+(?:\.\d+)?(?:\([a-zA-Z0-9]+\))*)"
)

# Michigan statutes: MCL 750.110a or M.C.L. § 750.110a
STATUTE_MCL = (
    r"(?:M\.?C\.?L\.?(?:A\.?)?\s*§?\s*"
    r"\d{1,4}\.\d{1,5}[a-z]?(?:\([a-zA-Z0-9]+\))*)"
)

# Public laws: Pub. L. No. 111-148 or Public Law 111-148
STATUTE_PUB_LAW = (
    r"(?:(?:Pub\.?\s*L\.?\s*No\.?|Public\s+Law)\s*\d{1,3}[-–]\d{1,4})"
)

# ---------------------------------------------------------------------------
# Constitutional provision patterns
# ---------------------------------------------------------------------------

CONST_US = (
    r"(?:U\.?\s*S\.?\s*Const\.?\s*"
    r"(?:art\.?\s*[IVX]+|[Aa]mend\.?\s*[IVX]+|\s*§\s*\d+)"
    r"(?:\s*,?\s*(?:§\s*\d+|cl\.?\s*\d+))*)"
)

CONST_MICH = (
    r"(?:(?:Mich\.?\s*|MI\s+)Const\.?\s*(?:(?:19|20)\d{2}\s*)?"
    r"(?:art\.?\s*[IVX]+\d*|[Aa]mend\.?\s*[IVX]+)"
    r"(?:\s*,?\s*§\s*\d+)*)"
)

# ---------------------------------------------------------------------------
# Court rule patterns
# ---------------------------------------------------------------------------

# Federal rules: Fed. R. Civ. P. 12(b)(6), Fed. R. App. P. 28
RULE_FEDERAL = (
    r"(?:Fed\.?\s*R\.?\s*"
    r"(?:Civ\.?\s*P\.?|App\.?\s*P\.?|Evid\.?|Crim\.?\s*P\.?|Bankr\.?\s*P\.?)"
    r"\s*\d{1,4}(?:\([a-zA-Z0-9]+\))*)"
)

# Michigan court rules: MCR 7.212(D) or Mich. Ct. R. 7.212
RULE_MICHIGAN = (
    r"(?:(?:MCR|MRE|MRCrP|M\.?C\.?R\.?|Mich\.?\s*(?:Ct\.?\s*)?R\.?)\s*"
    r"\d{1,2}\.\d{1,4}(?:\([A-Za-z0-9]+\))*)"
)

# Local rules: E.D. Mich. LR 7.1, W.D. Mich. LCivR 7.1
RULE_LOCAL = (
    r"(?:(?:[EWSN]\.?D\.?\s*(?:Mich|Tex|Cal|N\.?Y|Ill|Ohio|Pa)\.?\s*)"
    r"(?:LR|LCivR|LCrR|LBR)\s*\d{1,3}\.\d{1,3}(?:\([a-zA-Z0-9]+\))*)"
)

# ---------------------------------------------------------------------------
# Short-form patterns
# ---------------------------------------------------------------------------

# Id. / Ibid. with optional pincite
SHORT_ID = r"(?:Id\.(?:\s+at\s+\d{1,5}(?:[–\-]\d{1,5})?)?)"

# Supra: Smith, supra, at 123
SHORT_SUPRA = (
    r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?"
    r",?\s+supra"
    r"(?:,?\s+at\s+\d{1,5})?)"
)

# Short case pincite: 123 F.3d at 456
SHORT_CASE_PINCITE = rf"(?:\d{{1,4}}\s+{_ALL_REPORTERS_RE}\s+at\s+\d{{1,5}})"

# ---------------------------------------------------------------------------
# Other authority patterns
# ---------------------------------------------------------------------------

# Restatement: Restatement (Second) of Torts § 402A
OTHER_RESTATEMENT = (
    r"(?:Restatement\s*\([^)]+\)\s*(?:of\s+)?"
    r"[A-Z][a-zA-Z\s]+§\s*\d+[A-Z]?)"
)

# Law review: 123 Mich. L. Rev. 456 (2020)
OTHER_LAW_REVIEW = (
    r"(?:\d{1,3}\s+[A-Z][a-zA-Z.]+\s+(?:L\.?\s*(?:Rev|J)\.?|Law\s+(?:Review|Journal))"
    r"\s+\d{1,5}(?:\s*\(\d{4}\))?)"
)

# Treatise: Wright & Miller, Federal Practice § 1234
OTHER_TREATISE = (
    r"(?:[A-Z][a-z]+(?:\s*[&,]\s*[A-Z][a-z]+)+,?\s+"
    r"[A-Z][a-zA-Z\s]+§\s*\d+(?:\.\d+)?)"
)

# ---------------------------------------------------------------------------
# Pattern Registry — ordered list of (name, compiled_pattern, category)
# ---------------------------------------------------------------------------

PATTERN_REGISTRY: list[tuple[str, re.Pattern, CitationCategory]] = [
    # Cases (most specific first)
    ("case_parallel", re.compile(CASE_PARALLEL), CitationCategory.CASES),
    ("case_unpublished", re.compile(CASE_UNPUBLISHED), CitationCategory.CASES),
    ("case_full", re.compile(CASE_FULL), CitationCategory.CASES),
    # Statutes
    ("statute_usc", re.compile(STATUTE_USC), CitationCategory.STATUTES),
    ("statute_mcl", re.compile(STATUTE_MCL), CitationCategory.STATUTES),
    ("statute_pub_law", re.compile(STATUTE_PUB_LAW), CitationCategory.STATUTES),
    # Constitutional
    ("const_us", re.compile(CONST_US), CitationCategory.CONSTITUTIONAL),
    ("const_mich", re.compile(CONST_MICH), CitationCategory.CONSTITUTIONAL),
    # Rules
    ("rule_federal", re.compile(RULE_FEDERAL), CitationCategory.RULES),
    ("rule_michigan", re.compile(RULE_MICHIGAN), CitationCategory.RULES),
    ("rule_local", re.compile(RULE_LOCAL), CitationCategory.RULES),
    # Other authorities
    ("other_restatement", re.compile(OTHER_RESTATEMENT), CitationCategory.OTHER),
    ("other_law_review", re.compile(OTHER_LAW_REVIEW), CitationCategory.OTHER),
    ("other_treatise", re.compile(OTHER_TREATISE), CitationCategory.OTHER),
    # Short forms (last — resolved after full citations)
    ("short_id", re.compile(SHORT_ID), CitationCategory.CASES),
    ("short_supra", re.compile(SHORT_SUPRA), CitationCategory.CASES),
    ("short_case_pincite", re.compile(SHORT_CASE_PINCITE), CitationCategory.CASES),
]
