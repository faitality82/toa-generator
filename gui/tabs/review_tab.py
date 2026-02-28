"""Review tab — editable citation table with category filter, stats bar.

Displays all detected citations as CitationRow widgets in a scrollable frame.
Allows editing category, toggling primary, adding/removing citations.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from app.models import Citation, CitationCategory, TOAProject
from gui.theme import (
    BG_DARK, BG_DARKER, CATEGORY_COLORS, FONT_BODY, FONT_HEADING,
    FONT_SMALL, FONT_TINY, PRIMARY, PRIMARY_HOVER, SECONDARY,
    SUCCESS, TEXT_DIM, TEXT_PRIMARY, RADIUS_MD, RADIUS_SM,
    BTN_HEIGHT, BTN_WIDTH_SM,
)
from gui.widgets.citation_row import CitationRow


class ReviewTab(ctk.CTkFrame):
    """Citation review and editing tab."""

    def __init__(self, parent, project: TOAProject, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self.project = project
        self._filter_category: Optional[CitationCategory] = None
        self._rows: list[CitationRow] = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header with stats
        self._build_header()

        # Filter bar
        self._build_filter_bar()

        # Scrollable citation list
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color=BG_DARK, corner_radius=0,
        )
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.scroll_frame.grid_columnconfigure(0, weight=1)

        # Bottom action bar
        self._build_action_bar()

    def _build_header(self) -> None:
        """Build the header with title and stats."""
        header = ctk.CTkFrame(self, fg_color=BG_DARK)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="Review Citations",
            font=ctk.CTkFont(size=FONT_HEADING, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self.stats_var = ctk.StringVar(value="No citations loaded")
        ctk.CTkLabel(
            header,
            textvariable=self.stats_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=TEXT_DIM,
        ).grid(row=0, column=1, sticky="e")

    def _build_filter_bar(self) -> None:
        """Build category filter buttons."""
        bar = ctk.CTkFrame(self, fg_color=BG_DARK)
        bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 5))

        # "All" button
        self.all_btn = ctk.CTkButton(
            bar,
            text="All",
            width=60,
            height=28,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            font=ctk.CTkFont(size=FONT_TINY),
            command=lambda: self._set_filter(None),
        )
        self.all_btn.pack(side="left", padx=(0, 4))

        # Category buttons
        self._filter_btns: dict[CitationCategory, ctk.CTkButton] = {}
        for cat in CitationCategory:
            color = CATEGORY_COLORS.get(cat.value, SECONDARY)
            btn = ctk.CTkButton(
                bar,
                text=cat.value,
                width=120,
                height=28,
                fg_color=SECONDARY,
                hover_color=color,
                font=ctk.CTkFont(size=FONT_TINY),
                command=lambda c=cat: self._set_filter(c),
            )
            btn.pack(side="left", padx=2)
            self._filter_btns[cat] = btn

    def _build_action_bar(self) -> None:
        """Build bottom action bar with add button."""
        bar = ctk.CTkFrame(self, fg_color=BG_DARK)
        bar.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 10))

        ctk.CTkButton(
            bar,
            text="+ Add Citation",
            width=BTN_WIDTH_SM + 20,
            height=BTN_HEIGHT,
            fg_color=SECONDARY,
            hover_color=PRIMARY,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._add_citation,
        ).pack(side="left")

    def refresh(self) -> None:
        """Rebuild the citation list from project data."""
        # Clear existing rows
        for row in self._rows:
            row.destroy()
        self._rows.clear()

        # Filter citations
        citations = [c for c in self.project.citations if not c.is_short_form]
        if self._filter_category:
            citations = [c for c in citations if c.category == self._filter_category]

        # Sort by category then alphabetically
        citations.sort(key=lambda c: (c.category.sort_order, c.sort_key or ""))

        # Build rows
        for i, cite in enumerate(citations):
            row = CitationRow(
                self.scroll_frame,
                citation=cite,
                on_delete=self._delete_citation,
                on_change=self._on_citation_change,
            )
            row.grid(row=i, column=0, sticky="ew", pady=2)
            self._rows.append(row)

        # Update stats
        total = len([c for c in self.project.citations if not c.is_short_form])
        primary_count = len([c for c in self.project.citations if c.is_primary and not c.is_short_form])
        showing = len(citations)
        self.stats_var.set(
            f"{total} citations ({primary_count} primary) — showing {showing}"
        )

    def _set_filter(self, category: Optional[CitationCategory]) -> None:
        """Set the active category filter."""
        self._filter_category = category

        # Update button styles
        self.all_btn.configure(fg_color=PRIMARY if category is None else SECONDARY)
        for cat, btn in self._filter_btns.items():
            color = CATEGORY_COLORS.get(cat.value, SECONDARY)
            btn.configure(fg_color=color if cat == category else SECONDARY)

        self.refresh()

    def _delete_citation(self, citation: Citation) -> None:
        """Remove a citation from the project."""
        if citation in self.project.citations:
            self.project.citations.remove(citation)
        self.refresh()

    def _on_citation_change(self, citation: Citation) -> None:
        """Handle citation edit — update stats."""
        total = len([c for c in self.project.citations if not c.is_short_form])
        primary_count = len([c for c in self.project.citations if c.is_primary and not c.is_short_form])
        filtered = len(self._rows)
        self.stats_var.set(
            f"{total} citations ({primary_count} primary) — showing {filtered}"
        )

    def _add_citation(self) -> None:
        """Add a new blank citation."""
        new_cite = Citation(
            full_text="New Citation",
            display_name="New Citation",
            category=self._filter_category or CitationCategory.CASES,
            pages=[],
            confidence=1.0,
        )
        new_cite.generate_sort_key()
        self.project.citations.append(new_cite)
        self.refresh()
