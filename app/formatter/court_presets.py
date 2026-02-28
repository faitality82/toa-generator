"""Court-specific formatting presets for Table of Authorities.

Supports Michigan Court of Appeals, 6th Circuit, US Supreme Court,
and federal district courts (E.D./W.D. Michigan).
"""

from __future__ import annotations

from app.models import CitationCategory, CourtPreset

PRESETS: dict[str, CourtPreset] = {
    "michigan_coa": CourtPreset(
        name="Michigan Court of Appeals",
        code="michigan_coa",
        categories_order=[
            CitationCategory.CASES,
            CitationCategory.STATUTES,
            CitationCategory.CONSTITUTIONAL,
            CitationCategory.RULES,
            CitationCategory.OTHER,
        ],
        case_italics=True,
        primary_marker="*",
        font_name="Times New Roman",
        font_size_title=14,
        font_size_heading=12,
        font_size_body=12,
        hanging_indent_inches=0.5,
        tab_position_inches=6.5,
        notes="MCR 7.212(D)",
    ),
    "sixth_circuit": CourtPreset(
        name="Sixth Circuit Court of Appeals",
        code="sixth_circuit",
        categories_order=[
            CitationCategory.CASES,
            CitationCategory.STATUTES,
            CitationCategory.CONSTITUTIONAL,
            CitationCategory.RULES,
            CitationCategory.OTHER,
        ],
        case_italics=True,
        primary_marker="*",
        font_name="Times New Roman",
        font_size_title=14,
        font_size_heading=12,
        font_size_body=12,
        hanging_indent_inches=0.5,
        tab_position_inches=6.5,
        notes="6th Cir. R. 28(a)",
    ),
    "scotus": CourtPreset(
        name="Supreme Court of the United States",
        code="scotus",
        categories_order=[
            CitationCategory.CASES,
            CitationCategory.CONSTITUTIONAL,
            CitationCategory.STATUTES,
            CitationCategory.RULES,
            CitationCategory.OTHER,
        ],
        case_italics=True,
        primary_marker="*",
        font_name="Century Schoolbook",
        font_size_title=14,
        font_size_heading=12,
        font_size_body=12,
        hanging_indent_inches=0.5,
        tab_position_inches=6.5,
        notes="S. Ct. R. 34.1",
    ),
    "ed_michigan": CourtPreset(
        name="U.S. District Court, Eastern District of Michigan",
        code="ed_michigan",
        categories_order=[
            CitationCategory.CASES,
            CitationCategory.STATUTES,
            CitationCategory.CONSTITUTIONAL,
            CitationCategory.RULES,
            CitationCategory.OTHER,
        ],
        case_italics=True,
        primary_marker="*",
        font_name="Times New Roman",
        font_size_title=14,
        font_size_heading=12,
        font_size_body=12,
        hanging_indent_inches=0.5,
        tab_position_inches=6.5,
        notes="E.D. Mich. LR 7.1",
    ),
    "wd_michigan": CourtPreset(
        name="U.S. District Court, Western District of Michigan",
        code="wd_michigan",
        categories_order=[
            CitationCategory.CASES,
            CitationCategory.STATUTES,
            CitationCategory.CONSTITUTIONAL,
            CitationCategory.RULES,
            CitationCategory.OTHER,
        ],
        case_italics=True,
        primary_marker="*",
        font_name="Times New Roman",
        font_size_title=14,
        font_size_heading=12,
        font_size_body=12,
        hanging_indent_inches=0.5,
        tab_position_inches=6.5,
        notes="W.D. Mich. LCivR 7.1",
    ),
}

# Default preset
DEFAULT_PRESET = "michigan_coa"
