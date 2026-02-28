"""Generate tab — court preset selector, generate button, save dialog.

Runs TOAWriter in a daemon thread so the GUI stays responsive.
"""

from __future__ import annotations

import threading
from tkinter import filedialog

import customtkinter as ctk

from app.formatter.court_presets import PRESETS, DEFAULT_PRESET
from app.formatter.toa_writer import TOAWriter
from app.models import TOAProject
from gui.theme import (
    BG_DARK, BG_DARKER, FONT_BODY, FONT_HEADING, FONT_SMALL,
    PRIMARY, PRIMARY_HOVER, SECONDARY, SUCCESS, TEXT_DIM, TEXT_PRIMARY,
    RADIUS_MD, BTN_HEIGHT_LG, BTN_WIDTH_LG,
)


class GenerateTab(ctk.CTkFrame):
    """TOA generation tab."""

    def __init__(self, parent, project: TOAProject, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self.project = project

        self.grid_columnconfigure(0, weight=1)

        # Title
        ctk.CTkLabel(
            self,
            text="Generate Table of Authorities",
            font=ctk.CTkFont(size=FONT_HEADING, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, pady=(20, 5))

        ctk.CTkLabel(
            self,
            text="Select a court preset and generate the formatted TOA document",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, pady=(0, 20))

        # Court preset selector
        preset_frame = ctk.CTkFrame(self, fg_color=BG_DARKER, corner_radius=RADIUS_MD)
        preset_frame.grid(row=2, column=0, padx=40, pady=10, sticky="ew")
        preset_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            preset_frame,
            text="Court Preset:",
            font=ctk.CTkFont(size=FONT_BODY),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=(15, 10), pady=15)

        preset_names = {code: p.name for code, p in PRESETS.items()}
        self.preset_var = ctk.StringVar(value=PRESETS[DEFAULT_PRESET].name)
        self.preset_menu = ctk.CTkOptionMenu(
            preset_frame,
            values=list(preset_names.values()),
            variable=self.preset_var,
            width=350,
            height=35,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_preset_change,
        )
        self.preset_menu.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="ew")

        # Preset details
        self.preset_detail_var = ctk.StringVar(
            value=f"Rule: {PRESETS[DEFAULT_PRESET].notes}"
        )
        ctk.CTkLabel(
            self,
            textvariable=self.preset_detail_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=TEXT_DIM,
        ).grid(row=3, column=0, pady=5)

        # Citation summary
        self.summary_var = ctk.StringVar(value="No citations loaded")
        ctk.CTkLabel(
            self,
            textvariable=self.summary_var,
            font=ctk.CTkFont(size=FONT_BODY),
            text_color=TEXT_DIM,
        ).grid(row=4, column=0, pady=15)

        # Generate button
        self.generate_btn = ctk.CTkButton(
            self,
            text="Generate TOA Document",
            width=BTN_WIDTH_LG + 60,
            height=BTN_HEIGHT_LG,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            font=ctk.CTkFont(size=FONT_BODY, weight="bold"),
            command=self._generate,
        )
        self.generate_btn.grid(row=5, column=0, pady=20)

        # Status
        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=FONT_BODY),
            text_color=SUCCESS,
        ).grid(row=6, column=0, pady=10)

        # Set default preset
        self.project.preset = PRESETS[DEFAULT_PRESET]

    def refresh(self) -> None:
        """Update the citation summary."""
        citations = [c for c in self.project.citations if not c.is_short_form]
        if not citations:
            self.summary_var.set("No citations loaded")
            return

        from app.models import CitationCategory
        counts = {}
        for cat in CitationCategory:
            count = len([c for c in citations if c.category == cat])
            if count:
                counts[cat.value] = count

        parts = [f"{v} {k}" for k, v in counts.items()]
        total = sum(counts.values())
        self.summary_var.set(f"{total} citations: " + ", ".join(parts))

    def _on_preset_change(self, name: str) -> None:
        """Handle preset selection change."""
        for code, preset in PRESETS.items():
            if preset.name == name:
                self.project.preset = preset
                self.preset_detail_var.set(f"Rule: {preset.notes}")
                break

    def _generate(self) -> None:
        """Show save dialog and generate the TOA."""
        if not self.project.citations:
            self.status_var.set("No citations to generate from!")
            return

        output_path = filedialog.asksaveasfilename(
            title="Save Table of Authorities",
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile="Table_of_Authorities.docx",
        )
        if not output_path:
            return

        self.generate_btn.configure(state="disabled")
        self.status_var.set("Generating...")

        thread = threading.Thread(
            target=self._generate_worker, args=(output_path,), daemon=True
        )
        thread.start()

    def _generate_worker(self, output_path: str) -> None:
        """Background worker for TOA generation."""
        try:
            writer = TOAWriter(self.project)
            result_path = writer.generate(output_path)
            self.project.output_path = str(result_path)

            self.after(0, lambda: self.status_var.set(
                f"TOA saved to: {result_path.name}"
            ))
        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {e}"))
        finally:
            self.after(0, lambda: self.generate_btn.configure(state="normal"))
