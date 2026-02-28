"""Single citation row widget for the review table.

Layout: [* checkbox] [category dropdown] [citation entry] [pages label] [X delete]
"""

from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from app.models import Citation, CitationCategory
from gui.theme import (
    BG_DARK, BG_DARKER, CATEGORY_COLORS, DANGER, DANGER_HOVER,
    FONT_SMALL, FONT_TINY, PRIMARY, RADIUS_SM, TEXT_DIM, TEXT_PRIMARY,
)


class CitationRow(ctk.CTkFrame):
    """A single editable citation row."""

    def __init__(
        self,
        parent,
        citation: Citation,
        on_delete: Optional[Callable[[Citation], None]] = None,
        on_change: Optional[Callable[[Citation], None]] = None,
        **kwargs,
    ):
        super().__init__(parent, fg_color=BG_DARKER, corner_radius=RADIUS_SM, **kwargs)
        self.citation = citation
        self._on_delete = on_delete
        self._on_change = on_change

        self.grid_columnconfigure(2, weight=1)

        # Primary authority checkbox
        self.primary_var = ctk.BooleanVar(value=citation.is_primary)
        self.primary_cb = ctk.CTkCheckBox(
            self,
            text="*",
            variable=self.primary_var,
            width=40,
            checkbox_width=20,
            checkbox_height=20,
            fg_color=PRIMARY,
            font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            command=self._on_primary_toggle,
        )
        self.primary_cb.grid(row=0, column=0, padx=(8, 4), pady=6)

        # Category dropdown
        cat_values = [c.value for c in CitationCategory]
        self.category_var = ctk.StringVar(value=citation.category.value)
        self.category_menu = ctk.CTkOptionMenu(
            self,
            values=cat_values,
            variable=self.category_var,
            width=180,
            height=30,
            font=ctk.CTkFont(size=FONT_TINY),
            fg_color=self._cat_color(citation.category.value),
            button_color=self._cat_color(citation.category.value),
            command=self._on_category_change,
        )
        self.category_menu.grid(row=0, column=1, padx=4, pady=6)

        # Citation text entry
        self.cite_entry = ctk.CTkEntry(
            self,
            textvariable=ctk.StringVar(value=citation.display_name),
            font=ctk.CTkFont(size=FONT_SMALL),
            fg_color=BG_DARK,
            height=30,
        )
        self.cite_entry.grid(row=0, column=2, padx=4, pady=6, sticky="ew")
        self.cite_entry.bind("<FocusOut>", self._on_text_change)

        # Pages label
        self.pages_label = ctk.CTkLabel(
            self,
            text=citation.page_display or "—",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color=TEXT_DIM,
            width=80,
        )
        self.pages_label.grid(row=0, column=3, padx=4, pady=6)

        # Delete button
        self.delete_btn = ctk.CTkButton(
            self,
            text="✕",
            width=30,
            height=30,
            fg_color=DANGER,
            hover_color=DANGER_HOVER,
            font=ctk.CTkFont(size=FONT_TINY),
            command=self._on_delete_click,
        )
        self.delete_btn.grid(row=0, column=4, padx=(4, 8), pady=6)

    def _cat_color(self, cat_name: str) -> str:
        """Get the color for a category."""
        color = CATEGORY_COLORS.get(cat_name, PRIMARY)
        # Darken slightly for background use
        return color

    def _on_primary_toggle(self) -> None:
        self.citation.is_primary = self.primary_var.get()
        if self._on_change:
            self._on_change(self.citation)

    def _on_category_change(self, value: str) -> None:
        self.citation.category = CitationCategory(value)
        self.category_menu.configure(
            fg_color=self._cat_color(value),
            button_color=self._cat_color(value),
        )
        if self._on_change:
            self._on_change(self.citation)

    def _on_text_change(self, event=None) -> None:
        new_text = self.cite_entry.get()
        if new_text != self.citation.display_name:
            self.citation.display_name = new_text
            self.citation.generate_sort_key()
            if self._on_change:
                self._on_change(self.citation)

    def _on_delete_click(self) -> None:
        if self._on_delete:
            self._on_delete(self.citation)
