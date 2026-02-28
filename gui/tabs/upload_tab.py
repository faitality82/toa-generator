"""Upload tab — file picker, process button, progress bar, and cost calculator.

Runs citation detection in a daemon thread so the GUI stays responsive.
After detection, shows AI classification cost estimates across all models.
"""

from __future__ import annotations

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from app.ai_models import ALL_MODELS, MODELS_BY_PROVIDER, Provider, get_model
from app.config import settings
from app.cost_calculator import estimate_cost, estimate_all_models
from app.detection.detector import CitationDetector
from app.classifier.rule_classifier import reclassify, get_ambiguous
from app.classifier.ai_classifier import classify_ambiguous
from app.models import TOAProject
from app.parsers.docx_parser import parse_docx
from app.parsers.pdf_parser import parse_pdf
from gui.theme import (
    BG_DARK, BG_DARKER, CATEGORY_COLORS, FONT_BODY, FONT_HEADING,
    FONT_SMALL, FONT_TINY, INFO, PRIMARY, PRIMARY_HOVER, SECONDARY,
    SUCCESS, WARNING, TEXT_DIM, TEXT_PRIMARY,
    RADIUS_MD, RADIUS_SM, BTN_HEIGHT_LG, BTN_WIDTH_LG,
)


class UploadTab(ctk.CTkFrame):
    """File upload, citation detection, and cost estimation tab."""

    def __init__(self, parent, project: TOAProject, on_complete=None, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)
        self.project = project
        self._on_complete = on_complete
        self._doc_text = ""  # Full document text for cost estimation

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(8, weight=1)  # Let cost panel expand

        # Title
        ctk.CTkLabel(
            self,
            text="Upload Legal Brief",
            font=ctk.CTkFont(size=FONT_HEADING, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, pady=(20, 5))

        ctk.CTkLabel(
            self,
            text="Select a .docx or .pdf file to extract citations",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=TEXT_DIM,
        ).grid(row=1, column=0, pady=(0, 15))

        # File path display
        self.file_var = ctk.StringVar(value="No file selected")
        ctk.CTkLabel(
            self,
            textvariable=self.file_var,
            font=ctk.CTkFont(size=FONT_BODY),
            text_color=TEXT_DIM,
            wraplength=600,
        ).grid(row=2, column=0, padx=40, pady=5)

        # Buttons row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, pady=10)

        self.browse_btn = ctk.CTkButton(
            btn_frame,
            text="Browse Files",
            width=BTN_WIDTH_LG,
            height=BTN_HEIGHT_LG,
            fg_color=SECONDARY,
            hover_color=PRIMARY,
            font=ctk.CTkFont(size=FONT_BODY),
            command=self._browse,
        )
        self.browse_btn.pack(side="left", padx=10)

        self.process_btn = ctk.CTkButton(
            btn_frame,
            text="Detect Citations",
            width=BTN_WIDTH_LG + 40,
            height=BTN_HEIGHT_LG,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            font=ctk.CTkFont(size=FONT_BODY, weight="bold"),
            command=self._process,
            state="disabled",
        )
        self.process_btn.pack(side="left", padx=10)

        # Progress bar
        self.progress = ctk.CTkProgressBar(
            self, width=450, fg_color=BG_DARKER, progress_color=PRIMARY,
        )
        self.progress.grid(row=4, column=0, pady=8)
        self.progress.set(0)

        # Status label
        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=TEXT_DIM,
        ).grid(row=5, column=0, pady=3)

        # Results label
        self.results_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self,
            textvariable=self.results_var,
            font=ctk.CTkFont(size=FONT_BODY, weight="bold"),
            text_color=SUCCESS,
        ).grid(row=6, column=0, pady=5)

        # Active model cost (highlighted)
        self.active_cost_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self,
            textvariable=self.active_cost_var,
            font=ctk.CTkFont(size=FONT_BODY),
            text_color=WARNING,
        ).grid(row=7, column=0, pady=(0, 5))

        # --- Cost Calculator Panel (scrollable) ---
        self.cost_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=BG_DARKER,
            corner_radius=RADIUS_MD,
            label_text="💰 AI Classification Cost Estimates",
            label_font=ctk.CTkFont(size=FONT_SMALL, weight="bold"),
            label_fg_color=BG_DARKER,
        )
        self.cost_frame.grid(row=8, column=0, padx=20, pady=(5, 15), sticky="nsew")
        self.cost_frame.grid_columnconfigure(0, weight=1)

        # Placeholder text in cost panel
        self._cost_placeholder = ctk.CTkLabel(
            self.cost_frame,
            text="Process a document to see cost estimates across all AI models",
            font=ctk.CTkFont(size=FONT_TINY),
            text_color=TEXT_DIM,
        )
        self._cost_placeholder.grid(row=0, column=0, pady=10)

    def _browse(self) -> None:
        """Open file dialog for .docx or .pdf selection."""
        path = filedialog.askopenfilename(
            title="Select Legal Brief",
            filetypes=[
                ("Legal Documents", "*.docx *.pdf"),
                ("Word Documents", "*.docx"),
                ("PDF Files", "*.pdf"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self.file_var.set(path)
            self.project.source_path = path
            ext = Path(path).suffix.lower()
            self.project.source_type = ext.lstrip(".")
            self.process_btn.configure(state="normal")
            self.results_var.set("")
            self.active_cost_var.set("")

    def _process(self) -> None:
        """Start citation detection in a background thread."""
        self.process_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        self.progress.set(0)
        self.status_var.set("Parsing document...")
        self.results_var.set("")
        self.active_cost_var.set("")

        thread = threading.Thread(target=self._detect_worker, daemon=True)
        thread.start()

    def _detect_worker(self) -> None:
        """Background worker for citation detection."""
        try:
            path = self.project.source_path
            file_type = self.project.source_type

            # Step 1: Parse document
            self.after(0, lambda: self.progress.set(0.2))
            self.after(0, lambda: self.status_var.set("Parsing document..."))

            if file_type == "docx":
                pages = parse_docx(path)
            elif file_type == "pdf":
                pages = parse_pdf(path)
            else:
                self.after(0, lambda: self.status_var.set(f"Unsupported: {file_type}"))
                self._re_enable()
                return

            if not pages:
                self.after(0, lambda: self.status_var.set("No text found in document"))
                self._re_enable()
                return

            # Capture full text for cost estimation
            self._doc_text = "\n".join(p.text for p in pages)

            # Step 2: Detect citations
            self.after(0, lambda: self.progress.set(0.5))
            self.after(0, lambda: self.status_var.set("Detecting citations..."))

            detector = CitationDetector()
            citations = detector.detect(pages)

            # Step 3: Rule-based reclassification
            self.after(0, lambda: self.progress.set(0.7))
            self.after(0, lambda: self.status_var.set("Classifying citations..."))

            reclassify(citations)

            # Step 4: AI classification for ambiguous citations (if enabled)
            ambiguous = get_ambiguous(citations)
            if ambiguous and settings.ai_enabled:
                self.after(0, lambda: self.status_var.set(
                    f"AI classifying {len(ambiguous)} ambiguous citations..."
                ))
                classify_ambiguous(ambiguous)
            elif ambiguous and not settings.ai_enabled:
                n = len(ambiguous)
                self.after(0, lambda: self.status_var.set(
                    f"AI off — {n} ambiguous citation(s) kept with regex classification"
                ))

            self.after(0, lambda: self.progress.set(0.9))

            # Step 5: Store results
            self.project.citations = citations

            # Step 6: Update UI
            count = len([c for c in citations if not c.is_short_form])
            total_pages = len(pages)
            doc_chars = len(self._doc_text)

            self.after(0, lambda: self.progress.set(1.0))
            self.after(0, lambda: self.status_var.set("Detection complete!"))
            self.after(0, lambda: self.results_var.set(
                f"Found {count} unique citations across {total_pages} pages "
                f"({doc_chars:,} chars)"
            ))

            # Step 7: Calculate and display costs (or show AI-off message)
            ai_on = settings.ai_enabled
            n_ambiguous = len(ambiguous) if ambiguous else 0
            self.after(0, lambda: self._show_cost_estimates(count, ai_on, n_ambiguous))

            self._re_enable()

            # Notify parent
            if self._on_complete:
                self.after(0, self._on_complete)

        except Exception as e:
            self.after(0, lambda: self.status_var.set(f"Error: {e}"))
            self.after(0, lambda: self.progress.set(0))
            self._re_enable()

    def _re_enable(self) -> None:
        """Re-enable buttons from any thread."""
        self.after(0, lambda: self.process_btn.configure(state="normal"))
        self.after(0, lambda: self.browse_btn.configure(state="normal"))

    def _show_cost_estimates(
        self, citation_count: int, ai_enabled: bool = True, ambiguous_count: int = 0,
    ) -> None:
        """Build the cost comparison table in the cost panel."""
        # Clear existing content
        for widget in self.cost_frame.winfo_children():
            widget.destroy()

        if citation_count == 0:
            ctk.CTkLabel(
                self.cost_frame,
                text="No citations found — no AI classification cost.",
                font=ctk.CTkFont(size=FONT_TINY), text_color=TEXT_DIM,
            ).grid(row=0, column=0, pady=10)
            return

        # --- AI Disabled ---
        if not ai_enabled:
            self.active_cost_var.set("AI Classification: OFF — $0.00 (regex-only mode)")

            ctk.CTkLabel(
                self.cost_frame,
                text="🔒  AI Classification is OFF",
                font=ctk.CTkFont(size=FONT_BODY, weight="bold"),
                text_color=WARNING,
            ).grid(row=0, column=0, pady=(15, 5))

            msg_parts = [
                f"All {citation_count} citations classified using regex pattern matching.",
                "Cost: $0.00 — no API calls are made in this mode.",
            ]
            if ambiguous_count > 0:
                msg_parts.append(
                    f"\n{ambiguous_count} ambiguous citation(s) were classified by regex "
                    "with lower confidence. Enable AI in Settings to improve accuracy."
                )
            else:
                msg_parts.append(
                    "\nAll citations were confidently matched by regex patterns."
                )

            ctk.CTkLabel(
                self.cost_frame,
                text="\n".join(msg_parts),
                font=ctk.CTkFont(size=FONT_SMALL),
                text_color=TEXT_DIM,
                wraplength=550,
                justify="center",
            ).grid(row=1, column=0, pady=(5, 15), padx=20)

            ctk.CTkLabel(
                self.cost_frame,
                text="Tip: Toggle AI ON in the Settings tab to see cost estimates.",
                font=ctk.CTkFont(size=FONT_TINY),
                text_color=INFO,
            ).grid(row=2, column=0, pady=(0, 10))
            return

        # --- AI Enabled: show full cost table ---
        # Estimate costs across all models
        estimates = estimate_all_models(self._doc_text, citation_count)

        # Show active model cost prominently
        active_model = get_model(settings.ai_model)
        if active_model:
            active_est = estimate_cost(self._doc_text, citation_count, active_model)
            self.active_cost_var.set(
                f"Active model: {active_model.name} ({active_model.provider.value}) "
                f"— Est. cost: {active_est.cost_display} "
                f"({active_est.tokens_display} tokens)"
            )

        # Header row
        header = ctk.CTkFrame(self.cost_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 2))
        header.grid_columnconfigure(1, weight=1)

        for col, (text, w) in enumerate([
            ("Provider", 100), ("Model", 140), ("Input $/1M", 80),
            ("Output $/1M", 80), ("Est. Cost", 80), ("Tokens", 70),
        ]):
            ctk.CTkLabel(
                header, text=text, width=w,
                font=ctk.CTkFont(size=FONT_TINY, weight="bold"),
                text_color=TEXT_DIM, anchor="w",
            ).grid(row=0, column=col, padx=3)

        # Cost rows — grouped by provider
        row_idx = 1
        current_provider = None

        for est in estimates:
            m = est.model

            # Provider separator
            if m.provider != current_provider:
                current_provider = m.provider
                sep = ctk.CTkFrame(self.cost_frame, fg_color="gray30", height=1)
                sep.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=3)
                row_idx += 1

            # Highlight active model
            is_active = active_model and m.id == active_model.id
            row_bg = "gray25" if is_active else "transparent"

            rframe = ctk.CTkFrame(self.cost_frame, fg_color=row_bg, corner_radius=4)
            rframe.grid(row=row_idx, column=0, sticky="ew", padx=5, pady=1)

            # Recommended marker
            rec = " ⭐" if m.is_recommended else ""
            active_marker = " ◀" if is_active else ""

            for col, (text, w, color) in enumerate([
                (m.provider.value, 100, TEXT_DIM),
                (f"{m.name}{rec}{active_marker}", 140, TEXT_PRIMARY),
                (f"${m.input_price_per_m:.2f}", 80, TEXT_DIM),
                (f"${m.output_price_per_m:.2f}", 80, TEXT_DIM),
                (est.cost_display, 80, SUCCESS if est.total_cost < 0.01 else WARNING),
                (est.tokens_display, 70, TEXT_DIM),
            ]):
                ctk.CTkLabel(
                    rframe, text=text, width=w,
                    font=ctk.CTkFont(size=FONT_TINY),
                    text_color=color, anchor="w",
                ).grid(row=0, column=col, padx=3, pady=3)

            row_idx += 1

        # Footer note
        ctk.CTkLabel(
            self.cost_frame,
            text=(
                f"Estimates based on {citation_count} citations, "
                f"~{len(self._doc_text):,} chars. "
                "Actual cost depends on ambiguous citations sent to AI (typically 10-20%)."
            ),
            font=ctk.CTkFont(size=FONT_TINY),
            text_color=TEXT_DIM,
            wraplength=600,
        ).grid(row=row_idx, column=0, pady=(8, 5))
