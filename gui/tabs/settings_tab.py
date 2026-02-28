"""Settings tab — multi-provider AI model selection and API key management.

Supports: Anthropic, OpenAI, Google, Mistral, Cohere, DeepSeek, Meta (via API).
Saves all keys and model selection to .env for persistence.
"""

from __future__ import annotations

import sys
from pathlib import Path

import customtkinter as ctk

from app.ai_models import (
    AIModel, Provider, ALL_MODELS, MODELS_BY_PROVIDER,
    get_model, get_models_for_provider,
)
from app.config import settings
from gui.theme import (
    BG_DARK, BG_DARKER, FONT_BODY, FONT_HEADING, FONT_SMALL, FONT_TINY,
    PRIMARY, PRIMARY_HOVER, SECONDARY, SUCCESS, WARNING, ERROR,
    TEXT_DIM, TEXT_PRIMARY,
    RADIUS_MD, RADIUS_SM, BTN_HEIGHT, BTN_WIDTH_MD,
)

# PyInstaller-aware .env path
if getattr(sys, "frozen", False):
    ENV_PATH = Path(sys.executable).parent / ".env"
else:
    ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


class SettingsTab(ctk.CTkFrame):
    """Multi-provider AI settings tab."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color=BG_DARK, **kwargs)

        self.grid_columnconfigure(0, weight=1)

        # Scrollable container for all settings
        self.scroll = ctk.CTkScrollableFrame(self, fg_color=BG_DARK)
        self.scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.scroll.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        row = 0

        # Title
        ctk.CTkLabel(
            self.scroll,
            text="AI Model Settings",
            font=ctk.CTkFont(size=FONT_HEADING, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=row, column=0, pady=(15, 5)); row += 1

        ctk.CTkLabel(
            self.scroll,
            text="Select your AI provider, model, and manage API keys",
            font=ctk.CTkFont(size=FONT_SMALL),
            text_color=TEXT_DIM,
        ).grid(row=row, column=0, pady=(0, 15)); row += 1

        # --- AI Enabled Toggle ---
        toggle_frame = ctk.CTkFrame(self.scroll, fg_color=BG_DARKER, corner_radius=RADIUS_MD)
        toggle_frame.grid(row=row, column=0, padx=20, pady=(0, 12), sticky="ew"); row += 1
        toggle_frame.grid_columnconfigure(1, weight=1)

        self.ai_enabled_var = ctk.BooleanVar(value=settings.ai_enabled)
        self.ai_toggle = ctk.CTkSwitch(
            toggle_frame,
            text="AI Classification",
            variable=self.ai_enabled_var,
            font=ctk.CTkFont(size=FONT_BODY, weight="bold"),
            progress_color=PRIMARY,
            button_color="white",
            button_hover_color="gray90",
            command=self._on_ai_toggle,
            width=60,
        )
        self.ai_toggle.grid(row=0, column=0, padx=(15, 10), pady=12, sticky="w")

        self.toggle_status_var = ctk.StringVar()
        self._set_toggle_status_text()
        self.toggle_status_label = ctk.CTkLabel(
            toggle_frame,
            textvariable=self.toggle_status_var,
            font=ctk.CTkFont(size=FONT_SMALL),
        )
        self.toggle_status_label.grid(row=0, column=1, padx=(0, 15), pady=12, sticky="w")
        self._apply_toggle_status_color()

        # --- Provider + Model Selection ---
        model_frame = ctk.CTkFrame(self.scroll, fg_color=BG_DARKER, corner_radius=RADIUS_MD)
        model_frame.grid(row=row, column=0, padx=20, pady=8, sticky="ew"); row += 1
        model_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            model_frame, text="Provider:",
            font=ctk.CTkFont(size=FONT_BODY), text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, padx=(15, 10), pady=(15, 5), sticky="w")

        provider_names = [p.value for p in Provider]
        current_provider = settings.ai_provider or "Anthropic"
        self.provider_var = ctk.StringVar(value=current_provider)
        self.provider_menu = ctk.CTkOptionMenu(
            model_frame,
            values=provider_names,
            variable=self.provider_var,
            width=300,
            height=32,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_provider_change,
        )
        self.provider_menu.grid(row=0, column=1, padx=(0, 15), pady=(15, 5), sticky="ew")

        ctk.CTkLabel(
            model_frame, text="Model:",
            font=ctk.CTkFont(size=FONT_BODY), text_color=TEXT_PRIMARY,
        ).grid(row=1, column=0, padx=(15, 10), pady=(5, 5), sticky="w")

        self.model_var = ctk.StringVar(value="")
        self.model_menu = ctk.CTkOptionMenu(
            model_frame,
            values=[""],
            variable=self.model_var,
            width=300,
            height=32,
            fg_color=SECONDARY,
            button_color=PRIMARY,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._on_model_change,
        )
        self.model_menu.grid(row=1, column=1, padx=(0, 15), pady=(5, 5), sticky="ew")

        # Model details
        self.model_detail_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            model_frame, textvariable=self.model_detail_var,
            font=ctk.CTkFont(size=FONT_TINY), text_color=TEXT_DIM,
            wraplength=500, justify="left",
        ).grid(row=2, column=0, columnspan=2, padx=15, pady=(2, 10), sticky="w")

        # Pricing info
        self.pricing_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            model_frame, textvariable=self.pricing_var,
            font=ctk.CTkFont(size=FONT_TINY, weight="bold"), text_color=WARNING,
        ).grid(row=3, column=0, columnspan=2, padx=15, pady=(0, 15), sticky="w")

        # --- API Key Section ---
        key_label = ctk.CTkLabel(
            self.scroll, text="API Keys",
            font=ctk.CTkFont(size=FONT_BODY, weight="bold"), text_color=TEXT_PRIMARY,
        )
        key_label.grid(row=row, column=0, pady=(15, 5), sticky="w", padx=20); row += 1

        ctk.CTkLabel(
            self.scroll,
            text="Enter keys only for providers you want to use. Keys are saved to .env.",
            font=ctk.CTkFont(size=FONT_TINY), text_color=TEXT_DIM,
        ).grid(row=row, column=0, pady=(0, 10), sticky="w", padx=20); row += 1

        # Build API key entries for each provider
        self._key_entries: dict[str, ctk.CTkEntry] = {}
        _placeholders = {
            "Anthropic": "sk-ant-api03-...",
            "OpenAI": "sk-proj-...",
            "Google": "AIza...",
            "Mistral": "...",
            "Cohere": "...",
            "DeepSeek": "sk-...",
            "Meta (via API)": "Together AI key...",
        }

        for provider in Provider:
            pname = provider.value
            kf = ctk.CTkFrame(self.scroll, fg_color=BG_DARKER, corner_radius=RADIUS_SM)
            kf.grid(row=row, column=0, padx=20, pady=3, sticky="ew"); row += 1
            kf.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                kf, text=f"{pname}:",
                font=ctk.CTkFont(size=FONT_SMALL), text_color=TEXT_PRIMARY,
                width=120, anchor="w",
            ).grid(row=0, column=0, padx=(10, 5), pady=8)

            entry = ctk.CTkEntry(
                kf,
                placeholder_text=_placeholders.get(pname, "API key..."),
                show="*",
                font=ctk.CTkFont(size=FONT_TINY),
                fg_color=BG_DARK,
                height=30,
            )
            entry.grid(row=0, column=1, padx=(0, 10), pady=8, sticky="ew")

            # Pre-fill existing key
            existing_key = settings.get_api_key(pname)
            if existing_key:
                entry.insert(0, existing_key)

            self._key_entries[pname] = entry

        # Show/hide toggle
        self.show_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            self.scroll,
            text="Show API keys",
            variable=self.show_var,
            width=120,
            checkbox_width=20, checkbox_height=20,
            font=ctk.CTkFont(size=FONT_SMALL),
            command=self._toggle_show,
        ).grid(row=row, column=0, padx=20, pady=(5, 10), sticky="w"); row += 1

        # Save button
        ctk.CTkButton(
            self.scroll,
            text="Save All Settings",
            width=BTN_WIDTH_MD + 30,
            height=BTN_HEIGHT,
            fg_color=PRIMARY,
            hover_color=PRIMARY_HOVER,
            font=ctk.CTkFont(size=FONT_BODY, weight="bold"),
            command=self._save,
        ).grid(row=row, column=0, pady=15); row += 1

        # Status
        self.status_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            self.scroll, textvariable=self.status_var,
            font=ctk.CTkFont(size=FONT_SMALL), text_color=SUCCESS,
        ).grid(row=row, column=0, pady=5); row += 1

        # Info box
        info_frame = ctk.CTkFrame(self.scroll, fg_color=BG_DARKER, corner_radius=RADIUS_MD)
        info_frame.grid(row=row, column=0, padx=20, pady=(10, 20), sticky="ew"); row += 1

        ctk.CTkLabel(
            info_frame,
            text=(
                "API keys are optional. Without one, classification relies on\n"
                "regex patterns (handles 90%+ of citations). With a key, ambiguous\n"
                "citations are sent to your chosen AI model for classification.\n\n"
                "DeepSeek and Meta models use OpenAI-compatible APIs\n"
                "(Together AI / Fireworks for Meta, api.deepseek.com for DeepSeek)."
            ),
            font=ctk.CTkFont(size=FONT_TINY), text_color=TEXT_DIM,
            justify="left",
        ).pack(padx=15, pady=12)

        # Initialize model dropdown for current provider
        self._on_provider_change(current_provider)

        # Apply initial AI toggle state to controls
        self._update_ai_section_state()

    def _on_provider_change(self, provider_name: str) -> None:
        """Update model dropdown when provider changes."""
        try:
            provider = Provider(provider_name)
        except ValueError:
            return

        models = get_models_for_provider(provider)
        if not models:
            self.model_menu.configure(values=["No models available"])
            self.model_var.set("No models available")
            return

        model_labels = [f"{m.name}" for m in models]
        self.model_menu.configure(values=model_labels)

        # Try to keep current selection, else pick first
        current_model = get_model(settings.ai_model)
        if current_model and current_model.provider == provider:
            self.model_var.set(current_model.name)
        else:
            self.model_var.set(models[0].name)

        self._update_model_details()

    def _on_model_change(self, model_name: str) -> None:
        """Update model details display."""
        self._update_model_details()

    def _update_model_details(self) -> None:
        """Show description and pricing for the selected model."""
        model = self._get_selected_model()
        if not model:
            self.model_detail_var.set("")
            self.pricing_var.set("")
            return

        # Description + context window
        ctx = f"{model.context_window:,}" if model.context_window else "?"
        rec = " ⭐ RECOMMENDED" if model.is_recommended else ""
        self.model_detail_var.set(
            f"{model.description}  |  Context: {ctx} tokens{rec}"
        )
        self.pricing_var.set(f"💰 {model.price_summary}")

    def _get_selected_model(self) -> AIModel | None:
        """Get the AIModel object for the current selection."""
        model_name = self.model_var.get()
        provider_name = self.provider_var.get()
        try:
            provider = Provider(provider_name)
        except ValueError:
            return None
        for m in get_models_for_provider(provider):
            if m.name == model_name:
                return m
        return None

    def _toggle_show(self) -> None:
        """Toggle password visibility for all key entries."""
        show_char = "" if self.show_var.get() else "*"
        for entry in self._key_entries.values():
            entry.configure(show=show_char)

    def _on_ai_toggle(self) -> None:
        """Handle AI toggle switch change."""
        enabled = self.ai_enabled_var.get()
        settings.ai_enabled = enabled
        self._set_toggle_status_text()
        self._apply_toggle_status_color()
        self._update_ai_section_state()

    def _set_toggle_status_text(self) -> None:
        """Update the toggle label text based on current state."""
        if self.ai_enabled_var.get():
            self.toggle_status_var.set(
                "ON — Ambiguous citations sent to AI for classification"
            )
        else:
            self.toggle_status_var.set(
                "OFF — Regex-only mode (free, no API key needed)"
            )

    def _apply_toggle_status_color(self) -> None:
        """Set the toggle status label color."""
        if hasattr(self, "toggle_status_label"):
            color = SUCCESS if self.ai_enabled_var.get() else WARNING
            self.toggle_status_label.configure(text_color=color)

    def _update_ai_section_state(self) -> None:
        """Enable or disable the provider/model/key controls."""
        state = "normal" if self.ai_enabled_var.get() else "disabled"
        self.provider_menu.configure(state=state)
        self.model_menu.configure(state=state)
        for entry in self._key_entries.values():
            entry.configure(state=state)

    def _save(self) -> None:
        """Save all settings to .env file."""
        try:
            # Collect all settings
            env_data: dict[str, str] = {}

            # AI toggle
            env_data["AI_ENABLED"] = str(self.ai_enabled_var.get())
            settings.ai_enabled = self.ai_enabled_var.get()

            # API keys
            for pname, entry in self._key_entries.items():
                key = entry.get().strip()
                try:
                    provider = Provider(pname)
                    env_data[provider.env_key_name] = key
                    settings.set_api_key(pname, key)
                except ValueError:
                    pass

            # Model selection
            model = self._get_selected_model()
            if model:
                env_data["AI_MODEL"] = model.id
                env_data["AI_PROVIDER"] = model.provider.value
                settings.ai_model = model.id
                settings.ai_provider = model.provider.value

            # Read existing .env
            env_lines: list[str] = []
            if ENV_PATH.exists():
                env_lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

            # Update or add each key
            for env_key, env_val in env_data.items():
                found = False
                for i, line in enumerate(env_lines):
                    if line.split("=", 1)[0].strip() == env_key:
                        env_lines[i] = f"{env_key}={env_val}"
                        found = True
                        break
                if not found:
                    env_lines.append(f"{env_key}={env_val}")

            # Write back
            ENV_PATH.write_text("\n".join(env_lines) + "\n", encoding="utf-8")

            ai_state = "ON" if settings.ai_enabled else "OFF"
            model_display = model.display_label if model else "None"
            self.status_var.set(
                f"✓ Settings saved! AI: {ai_state} | Model: {model_display}"
            )
        except Exception as e:
            self.status_var.set(f"Error saving: {e}")
