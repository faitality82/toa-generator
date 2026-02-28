"""Main application window for TOA Generator.

Dark-themed CustomTkinter app with tabview:
Upload → Review → Generate → Settings
"""

from __future__ import annotations

import customtkinter as ctk

from app.models import TOAProject
from gui.theme import BG_DARK, BG_DARKER, FONT_BODY, PRIMARY, TEXT_PRIMARY
from gui.tabs.upload_tab import UploadTab
from gui.tabs.review_tab import ReviewTab
from gui.tabs.generate_tab import GenerateTab
from gui.tabs.settings_tab import SettingsTab


class TOAGeneratorApp(ctk.CTk):
    """TOA Generator main application window."""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("TOA Generator — Table of Authorities")
        self.geometry("1100x750")
        self.minsize(900, 600)

        # Dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG_DARK)

        # Shared project state
        self.project = TOAProject()

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Tab view
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=BG_DARK,
            segmented_button_fg_color=BG_DARKER,
            segmented_button_selected_color=PRIMARY,
            segmented_button_unselected_color=BG_DARKER,
        )
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Create tabs
        self.tabview.add("Upload")
        self.tabview.add("Review")
        self.tabview.add("Generate")
        self.tabview.add("Settings")

        # Populate tabs
        self.upload_tab = UploadTab(
            self.tabview.tab("Upload"),
            project=self.project,
            on_complete=self._on_detection_complete,
        )
        self.upload_tab.pack(fill="both", expand=True)

        self.review_tab = ReviewTab(
            self.tabview.tab("Review"),
            project=self.project,
        )
        self.review_tab.pack(fill="both", expand=True)

        self.generate_tab = GenerateTab(
            self.tabview.tab("Generate"),
            project=self.project,
        )
        self.generate_tab.pack(fill="both", expand=True)

        self.settings_tab = SettingsTab(
            self.tabview.tab("Settings"),
        )
        self.settings_tab.pack(fill="both", expand=True)

        # Start on Upload tab
        self.tabview.set("Upload")

    def _on_detection_complete(self) -> None:
        """Called when citation detection finishes — switch to Review tab."""
        self.review_tab.refresh()
        self.generate_tab.refresh()
        self.tabview.set("Review")
