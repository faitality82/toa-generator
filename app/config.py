"""Application configuration loaded from environment variables."""

import sys
from pathlib import Path
from pydantic_settings import BaseSettings

# PyInstaller-aware .env path: next to .exe when frozen, else project root
if getattr(sys, "frozen", False):
    _env_file = str(Path(sys.executable).parent / ".env")
else:
    _env_file = str(Path(__file__).resolve().parent.parent / ".env")


class Settings(BaseSettings):
    # Provider API keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    google_api_key: str = ""
    mistral_api_key: str = ""
    cohere_api_key: str = ""
    deepseek_api_key: str = ""
    meta_api_key: str = ""  # Together AI / Fireworks key for Meta models

    # AI toggle — when False, only rule-based regex classification is used
    ai_enabled: bool = True

    # Active model selection
    ai_model: str = "claude-sonnet-4-20250514"
    ai_provider: str = "Anthropic"

    # Meta/Together AI base URL (for OpenAI-compatible endpoints)
    meta_base_url: str = "https://api.together.xyz/v1"
    deepseek_base_url: str = "https://api.deepseek.com"

    model_config = {
        "env_file": _env_file,
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_api_key(self, provider_name: str) -> str:
        """Get the API key for a provider by name."""
        key_map = {
            "Anthropic": self.anthropic_api_key,
            "OpenAI": self.openai_api_key,
            "Google": self.google_api_key,
            "Mistral": self.mistral_api_key,
            "Cohere": self.cohere_api_key,
            "DeepSeek": self.deepseek_api_key,
            "Meta (via API)": self.meta_api_key,
        }
        return key_map.get(provider_name, "")

    def set_api_key(self, provider_name: str, key: str) -> None:
        """Set the API key for a provider by name."""
        attr_map = {
            "Anthropic": "anthropic_api_key",
            "OpenAI": "openai_api_key",
            "Google": "google_api_key",
            "Mistral": "mistral_api_key",
            "Cohere": "cohere_api_key",
            "DeepSeek": "deepseek_api_key",
            "Meta (via API)": "meta_api_key",
        }
        attr = attr_map.get(provider_name)
        if attr:
            setattr(self, attr, key)


settings = Settings()
