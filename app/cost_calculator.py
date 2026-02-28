"""Cost calculator for AI-powered citation classification.

Estimates token usage from document text and calculates cost per model.
Uses a ~4 chars/token heuristic (standard for English text).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.ai_models import AIModel, ALL_MODELS, DEFAULT_MODEL


# Approximate characters per token for English legal text
CHARS_PER_TOKEN = 4

# System prompt overhead (tokens) — the classification instructions
SYSTEM_PROMPT_TOKENS = 200

# Output estimate: ~50 tokens per citation for JSON classification response
OUTPUT_TOKENS_PER_CITATION = 50


@dataclass
class CostEstimate:
    """Cost estimate for processing a document with a specific model."""

    model: AIModel
    input_tokens: int
    output_tokens: int
    total_tokens: int
    input_cost: float  # USD
    output_cost: float  # USD
    total_cost: float  # USD
    citation_count: int
    document_chars: int

    @property
    def cost_display(self) -> str:
        """Formatted cost string."""
        if self.total_cost < 0.01:
            return f"${self.total_cost:.4f}"
        return f"${self.total_cost:.2f}"

    @property
    def tokens_display(self) -> str:
        """Formatted token count."""
        if self.total_tokens >= 1_000_000:
            return f"{self.total_tokens / 1_000_000:.1f}M"
        if self.total_tokens >= 1_000:
            return f"{self.total_tokens / 1_000:.1f}K"
        return str(self.total_tokens)


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using character-based heuristic.

    For legal English text, ~4 characters per token is a reasonable estimate.
    This slightly overestimates to give a conservative cost figure.
    """
    return max(1, len(text) // CHARS_PER_TOKEN)


def estimate_cost(
    document_text: str,
    citation_count: int,
    model: AIModel | None = None,
) -> CostEstimate:
    """Estimate the cost of classifying citations for a document.

    The AI classifier sends the citation text (not the full document) to the API.
    Only ambiguous citations (~10-20% of total) get sent for AI classification.

    Args:
        document_text: Full text of the document (for context estimation).
        citation_count: Number of detected citations.
        model: AI model to use (defaults to DEFAULT_MODEL).

    Returns:
        CostEstimate with token counts and costs.
    """
    if model is None:
        model = DEFAULT_MODEL

    # Estimate: AI classifier sends citation list + system prompt
    # Approximate the citation text as ~10% of document (citation strings only)
    citation_text_chars = len(document_text) // 10
    input_tokens = estimate_tokens_for_classification(citation_text_chars, citation_count)
    output_tokens = citation_count * OUTPUT_TOKENS_PER_CITATION

    total_tokens = input_tokens + output_tokens
    input_cost = input_tokens * model.input_price_per_token
    output_cost = output_tokens * model.output_price_per_token

    return CostEstimate(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=input_cost + output_cost,
        citation_count=citation_count,
        document_chars=len(document_text),
    )


def estimate_tokens_for_classification(
    citation_text_chars: int,
    citation_count: int,
) -> int:
    """Estimate input tokens for the classification API call.

    Includes system prompt + numbered citation list.
    """
    # System prompt tokens
    tokens = SYSTEM_PROMPT_TOKENS

    # Citation text tokens (the actual citations being classified)
    tokens += max(1, citation_text_chars // CHARS_PER_TOKEN)

    # Numbering/formatting overhead (~5 tokens per citation for "1. ", "2. " etc.)
    tokens += citation_count * 5

    return tokens


def estimate_all_models(
    document_text: str,
    citation_count: int,
) -> list[CostEstimate]:
    """Estimate costs across all available models, sorted by total cost.

    Args:
        document_text: Full document text.
        citation_count: Number of detected citations.

    Returns:
        List of CostEstimate sorted from cheapest to most expensive.
    """
    estimates = [
        estimate_cost(document_text, citation_count, model)
        for model in ALL_MODELS
    ]
    estimates.sort(key=lambda e: e.total_cost)
    return estimates


def estimate_full_document_cost(
    document_text: str,
    model: AIModel | None = None,
) -> CostEstimate:
    """Estimate cost if the entire document were sent to AI (worst case).

    This is the upper bound — useful for showing maximum possible cost.
    In practice, only ambiguous citations are sent.
    """
    if model is None:
        model = DEFAULT_MODEL

    input_tokens = SYSTEM_PROMPT_TOKENS + estimate_tokens(document_text)
    # Assume generous output
    output_tokens = max(500, input_tokens // 5)
    total_tokens = input_tokens + output_tokens

    return CostEstimate(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        input_cost=input_tokens * model.input_price_per_token,
        output_cost=output_tokens * model.output_price_per_token,
        total_cost=(input_tokens * model.input_price_per_token
                    + output_tokens * model.output_price_per_token),
        citation_count=0,
        document_chars=len(document_text),
    )
