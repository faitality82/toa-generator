"""AI-powered classification for ambiguous citations — multi-provider support.

Supports: Anthropic, OpenAI, Google, Mistral, Cohere, DeepSeek, Meta (via API).
Only called for citations flagged as low-confidence by the rule classifier.
"""

from __future__ import annotations

import json
import logging

from app.ai_models import AIModel, Provider, get_model, DEFAULT_MODEL
from app.config import settings
from app.models import Citation, CitationCategory

logger = logging.getLogger(__name__)

# Category mapping for AI responses
_CATEGORY_MAP = {
    "cases": CitationCategory.CASES,
    "statutes": CitationCategory.STATUTES,
    "constitutional": CitationCategory.CONSTITUTIONAL,
    "constitutional provisions": CitationCategory.CONSTITUTIONAL,
    "rules": CitationCategory.RULES,
    "other": CitationCategory.OTHER,
    "other authorities": CitationCategory.OTHER,
}

_SYSTEM_PROMPT = """You are a legal citation classifier. Given a list of legal citations,
classify each into one of these categories:
- Cases (court opinions, judicial decisions)
- Statutes (federal/state statutes, codes, public laws)
- Constitutional Provisions (US or state constitution articles/amendments)
- Rules (court rules, rules of procedure, rules of evidence)
- Other Authorities (treatises, law review articles, restatements, secondary sources)

Respond with a JSON array of objects, each with "index" (0-based) and "category" fields.
Only use the exact category names listed above."""


def classify_ambiguous(citations: list[Citation]) -> list[Citation]:
    """Send ambiguous citations to the selected AI model for classification.

    Uses the model configured in settings (ai_model + ai_provider).

    Args:
        citations: Low-confidence citations to classify.

    Returns:
        The same list with updated categories and confidence scores.
    """
    if not citations:
        return citations

    # Determine the active model
    model = get_model(settings.ai_model) or DEFAULT_MODEL
    api_key = settings.get_api_key(model.provider.value)

    if not api_key:
        logger.warning(
            "No API key configured for %s; skipping AI classification",
            model.provider.value,
        )
        return citations

    # Build the prompt
    citation_list = "\n".join(
        f"{i}. {c.full_text}" for i, c in enumerate(citations)
    )
    user_prompt = f"Classify these legal citations:\n\n{citation_list}"

    # Dispatch to the appropriate provider
    try:
        response_text = _call_provider(model, api_key, user_prompt)
        if response_text:
            _apply_classifications(citations, response_text)
    except Exception as e:
        logger.error("AI classification failed (%s): %s", model.provider.value, e)

    return citations


def _call_provider(model: AIModel, api_key: str, user_prompt: str) -> str | None:
    """Route the API call to the correct provider."""
    provider = model.provider

    if provider == Provider.ANTHROPIC:
        return _call_anthropic(model, api_key, user_prompt)
    elif provider == Provider.OPENAI:
        return _call_openai(model, api_key, user_prompt)
    elif provider == Provider.GOOGLE:
        return _call_google(model, api_key, user_prompt)
    elif provider == Provider.MISTRAL:
        return _call_mistral(model, api_key, user_prompt)
    elif provider == Provider.COHERE:
        return _call_cohere(model, api_key, user_prompt)
    elif provider == Provider.DEEPSEEK:
        return _call_openai_compatible(
            model, api_key, user_prompt, base_url=settings.deepseek_base_url
        )
    elif provider == Provider.META:
        return _call_openai_compatible(
            model, api_key, user_prompt, base_url=settings.meta_base_url
        )
    else:
        logger.error("Unsupported provider: %s", provider.value)
        return None


# ---------------------------------------------------------------------------
# Provider implementations
# ---------------------------------------------------------------------------


def _call_anthropic(model: AIModel, api_key: str, user_prompt: str) -> str | None:
    """Call Anthropic Claude API."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model.id,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text


def _call_openai(model: AIModel, api_key: str, user_prompt: str) -> str | None:
    """Call OpenAI API."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model.id,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _call_openai_compatible(
    model: AIModel, api_key: str, user_prompt: str, base_url: str
) -> str | None:
    """Call an OpenAI-compatible API (DeepSeek, Together AI / Meta, etc.)."""
    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=base_url)
    response = client.chat.completions.create(
        model=model.id,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _call_google(model: AIModel, api_key: str, user_prompt: str) -> str | None:
    """Call Google Gemini API (new google-genai SDK)."""
    from google import genai
    from google.genai.types import GenerateContentConfig

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model.id,
        contents=user_prompt,
        config=GenerateContentConfig(
            system_instruction=_SYSTEM_PROMPT,
            max_output_tokens=1024,
        ),
    )
    return response.text


def _call_mistral(model: AIModel, api_key: str, user_prompt: str) -> str | None:
    """Call Mistral API."""
    from mistralai import Mistral

    client = Mistral(api_key=api_key)
    response = client.chat.complete(
        model=model.id,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def _call_cohere(model: AIModel, api_key: str, user_prompt: str) -> str | None:
    """Call Cohere API."""
    import cohere

    client = cohere.ClientV2(api_key=api_key)
    response = client.chat(
        model=model.id,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1024,
    )
    return response.message.content[0].text


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


def _apply_classifications(citations: list[Citation], response_text: str) -> None:
    """Parse the AI's JSON response and apply categories."""
    try:
        text = response_text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        results = json.loads(text)

        for item in results:
            idx = item.get("index", -1)
            cat_name = item.get("category", "").lower()

            if 0 <= idx < len(citations) and cat_name in _CATEGORY_MAP:
                citations[idx].category = _CATEGORY_MAP[cat_name]
                citations[idx].confidence = 0.85

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Failed to parse AI classification response: %s", e)
