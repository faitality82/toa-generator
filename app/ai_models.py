"""Enterprise AI model definitions with pricing.

Covers all major providers: Anthropic, OpenAI, Google, Mistral, Meta (via API),
Cohere, DeepSeek, and Amazon Bedrock wrappers. Prices are per 1M tokens.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Provider(str, Enum):
    """AI provider companies."""

    ANTHROPIC = "Anthropic"
    OPENAI = "OpenAI"
    GOOGLE = "Google"
    MISTRAL = "Mistral"
    COHERE = "Cohere"
    DEEPSEEK = "DeepSeek"
    META = "Meta (via API)"

    @property
    def env_key_name(self) -> str:
        """Environment variable name for this provider's API key."""
        return {
            Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
            Provider.OPENAI: "OPENAI_API_KEY",
            Provider.GOOGLE: "GOOGLE_API_KEY",
            Provider.MISTRAL: "MISTRAL_API_KEY",
            Provider.COHERE: "COHERE_API_KEY",
            Provider.DEEPSEEK: "DEEPSEEK_API_KEY",
            Provider.META: "META_API_KEY",
        }[self]

    @property
    def package_name(self) -> str:
        """Python package required for this provider."""
        return {
            Provider.ANTHROPIC: "anthropic",
            Provider.OPENAI: "openai",
            Provider.GOOGLE: "google-genai",
            Provider.MISTRAL: "mistralai",
            Provider.COHERE: "cohere",
            Provider.DEEPSEEK: "openai",  # DeepSeek uses OpenAI-compatible API
            Provider.META: "openai",  # Meta via compatible endpoints
        }[self]


@dataclass
class AIModel:
    """An AI model with pricing and metadata."""

    id: str  # API model identifier (e.g., "claude-sonnet-4-20250514")
    name: str  # Display name (e.g., "Claude Sonnet 4")
    provider: Provider
    input_price_per_m: float  # USD per 1M input tokens
    output_price_per_m: float  # USD per 1M output tokens
    context_window: int  # Max tokens
    description: str = ""
    is_recommended: bool = False  # Best value for TOA classification task

    @property
    def input_price_per_token(self) -> float:
        return self.input_price_per_m / 1_000_000

    @property
    def output_price_per_token(self) -> float:
        return self.output_price_per_m / 1_000_000

    @property
    def display_label(self) -> str:
        return f"{self.name} ({self.provider.value})"

    @property
    def price_summary(self) -> str:
        return f"${self.input_price_per_m:.2f} / ${self.output_price_per_m:.2f} per 1M tokens (in/out)"


# ---------------------------------------------------------------------------
# Anthropic Models
# ---------------------------------------------------------------------------

CLAUDE_OPUS_4 = AIModel(
    id="claude-opus-4-20250514",
    name="Claude Opus 4",
    provider=Provider.ANTHROPIC,
    input_price_per_m=15.00,
    output_price_per_m=75.00,
    context_window=200_000,
    description="Most capable, best for complex legal reasoning",
)

CLAUDE_SONNET_4 = AIModel(
    id="claude-sonnet-4-20250514",
    name="Claude Sonnet 4",
    provider=Provider.ANTHROPIC,
    input_price_per_m=3.00,
    output_price_per_m=15.00,
    context_window=200_000,
    description="Excellent balance of quality and cost",
    is_recommended=True,
)

CLAUDE_HAIKU_35 = AIModel(
    id="claude-3-5-haiku-20241022",
    name="Claude 3.5 Haiku",
    provider=Provider.ANTHROPIC,
    input_price_per_m=0.80,
    output_price_per_m=4.00,
    context_window=200_000,
    description="Fast and affordable for simple classification",
)

# ---------------------------------------------------------------------------
# OpenAI Models
# ---------------------------------------------------------------------------

GPT_4O = AIModel(
    id="gpt-4o",
    name="GPT-4o",
    provider=Provider.OPENAI,
    input_price_per_m=2.50,
    output_price_per_m=10.00,
    context_window=128_000,
    description="OpenAI's flagship multimodal model",
)

GPT_4O_MINI = AIModel(
    id="gpt-4o-mini",
    name="GPT-4o Mini",
    provider=Provider.OPENAI,
    input_price_per_m=0.15,
    output_price_per_m=0.60,
    context_window=128_000,
    description="Most affordable OpenAI model",
)

GPT_O1 = AIModel(
    id="o1",
    name="o1",
    provider=Provider.OPENAI,
    input_price_per_m=15.00,
    output_price_per_m=60.00,
    context_window=200_000,
    description="Advanced reasoning model",
)

GPT_O1_MINI = AIModel(
    id="o1-mini",
    name="o1-mini",
    provider=Provider.OPENAI,
    input_price_per_m=3.00,
    output_price_per_m=12.00,
    context_window=128_000,
    description="Smaller reasoning model",
)

GPT_O3_MINI = AIModel(
    id="o3-mini",
    name="o3-mini",
    provider=Provider.OPENAI,
    input_price_per_m=1.10,
    output_price_per_m=4.40,
    context_window=200_000,
    description="Cost-effective reasoning",
)

GPT_4_TURBO = AIModel(
    id="gpt-4-turbo",
    name="GPT-4 Turbo",
    provider=Provider.OPENAI,
    input_price_per_m=10.00,
    output_price_per_m=30.00,
    context_window=128_000,
    description="Previous generation flagship",
)

# ---------------------------------------------------------------------------
# Google Models
# ---------------------------------------------------------------------------

GEMINI_20_FLASH = AIModel(
    id="gemini-2.0-flash",
    name="Gemini 2.0 Flash",
    provider=Provider.GOOGLE,
    input_price_per_m=0.10,
    output_price_per_m=0.40,
    context_window=1_000_000,
    description="Fast and very affordable with huge context",
)

GEMINI_15_PRO = AIModel(
    id="gemini-1.5-pro",
    name="Gemini 1.5 Pro",
    provider=Provider.GOOGLE,
    input_price_per_m=1.25,
    output_price_per_m=5.00,
    context_window=2_000_000,
    description="Google's premium model with largest context window",
)

GEMINI_15_FLASH = AIModel(
    id="gemini-1.5-flash",
    name="Gemini 1.5 Flash",
    provider=Provider.GOOGLE,
    input_price_per_m=0.075,
    output_price_per_m=0.30,
    context_window=1_000_000,
    description="Most affordable Google model",
)

# ---------------------------------------------------------------------------
# Mistral Models
# ---------------------------------------------------------------------------

MISTRAL_LARGE = AIModel(
    id="mistral-large-latest",
    name="Mistral Large",
    provider=Provider.MISTRAL,
    input_price_per_m=2.00,
    output_price_per_m=6.00,
    context_window=128_000,
    description="Mistral's most capable model",
)

MISTRAL_SMALL = AIModel(
    id="mistral-small-latest",
    name="Mistral Small",
    provider=Provider.MISTRAL,
    input_price_per_m=0.20,
    output_price_per_m=0.60,
    context_window=128_000,
    description="Fast and affordable Mistral model",
)

CODESTRAL = AIModel(
    id="codestral-latest",
    name="Codestral",
    provider=Provider.MISTRAL,
    input_price_per_m=0.30,
    output_price_per_m=0.90,
    context_window=256_000,
    description="Optimized for code and structured output",
)

# ---------------------------------------------------------------------------
# Cohere Models
# ---------------------------------------------------------------------------

COMMAND_R_PLUS = AIModel(
    id="command-r-plus",
    name="Command R+",
    provider=Provider.COHERE,
    input_price_per_m=2.50,
    output_price_per_m=10.00,
    context_window=128_000,
    description="Cohere's premium enterprise model",
)

COMMAND_R = AIModel(
    id="command-r",
    name="Command R",
    provider=Provider.COHERE,
    input_price_per_m=0.15,
    output_price_per_m=0.60,
    context_window=128_000,
    description="Efficient enterprise model",
)

# ---------------------------------------------------------------------------
# DeepSeek Models
# ---------------------------------------------------------------------------

DEEPSEEK_V3 = AIModel(
    id="deepseek-chat",
    name="DeepSeek V3",
    provider=Provider.DEEPSEEK,
    input_price_per_m=0.27,
    output_price_per_m=1.10,
    context_window=64_000,
    description="High quality at very low cost",
)

DEEPSEEK_REASONER = AIModel(
    id="deepseek-reasoner",
    name="DeepSeek R1",
    provider=Provider.DEEPSEEK,
    input_price_per_m=0.55,
    output_price_per_m=2.19,
    context_window=64_000,
    description="Reasoning-focused model",
)

# ---------------------------------------------------------------------------
# Meta Models (via OpenAI-compatible APIs like Together, Fireworks, etc.)
# ---------------------------------------------------------------------------

LLAMA_31_405B = AIModel(
    id="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
    name="Llama 3.1 405B",
    provider=Provider.META,
    input_price_per_m=3.50,
    output_price_per_m=3.50,
    context_window=128_000,
    description="Meta's largest open model (via Together AI)",
)

LLAMA_31_70B = AIModel(
    id="meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
    name="Llama 3.1 70B",
    provider=Provider.META,
    input_price_per_m=0.88,
    output_price_per_m=0.88,
    context_window=128_000,
    description="Strong mid-size open model (via Together AI)",
)

LLAMA_31_8B = AIModel(
    id="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    name="Llama 3.1 8B",
    provider=Provider.META,
    input_price_per_m=0.18,
    output_price_per_m=0.18,
    context_window=128_000,
    description="Lightweight open model (via Together AI)",
)

# ---------------------------------------------------------------------------
# Registry — all models in recommended display order
# ---------------------------------------------------------------------------

ALL_MODELS: list[AIModel] = [
    # Anthropic
    CLAUDE_SONNET_4,
    CLAUDE_OPUS_4,
    CLAUDE_HAIKU_35,
    # OpenAI
    GPT_4O,
    GPT_4O_MINI,
    GPT_O1,
    GPT_O1_MINI,
    GPT_O3_MINI,
    GPT_4_TURBO,
    # Google
    GEMINI_20_FLASH,
    GEMINI_15_PRO,
    GEMINI_15_FLASH,
    # Mistral
    MISTRAL_LARGE,
    MISTRAL_SMALL,
    CODESTRAL,
    # Cohere
    COMMAND_R_PLUS,
    COMMAND_R,
    # DeepSeek
    DEEPSEEK_V3,
    DEEPSEEK_REASONER,
    # Meta
    LLAMA_31_405B,
    LLAMA_31_70B,
    LLAMA_31_8B,
]

# Quick lookups
MODELS_BY_ID: dict[str, AIModel] = {m.id: m for m in ALL_MODELS}
MODELS_BY_PROVIDER: dict[Provider, list[AIModel]] = {}
for _m in ALL_MODELS:
    MODELS_BY_PROVIDER.setdefault(_m.provider, []).append(_m)

DEFAULT_MODEL = CLAUDE_SONNET_4


def get_model(model_id: str) -> AIModel | None:
    """Look up a model by its API identifier."""
    return MODELS_BY_ID.get(model_id)


def get_models_for_provider(provider: Provider) -> list[AIModel]:
    """Get all models for a given provider."""
    return MODELS_BY_PROVIDER.get(provider, [])


def get_recommended_models() -> list[AIModel]:
    """Get models flagged as recommended for the TOA classification task."""
    return [m for m in ALL_MODELS if m.is_recommended]
