"""
Async Gemini client for Lexora.

Includes concurrency control, retry only for transient failures, and explicit
classification for permanent Gemini/API configuration errors.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

import google.generativeai as genai
from pydantic import ValidationError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from app.config import get_settings
from app.models import GeneratedCopy, GeneratedVariations

logger = logging.getLogger("gemini_client")

_settings = get_settings()
genai.configure(api_key=_settings.gemini_api_key)
_semaphore = asyncio.Semaphore(_settings.max_concurrent_requests)

_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "variations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "style": {"type": "string"},
                    "headline": {"type": "string"},
                    "body": {"type": "string"},
                    "hashtags": {"type": "array", "items": {"type": "string"}},
                    "call_to_action": {"type": "string"},
                },
                "required": ["style", "headline", "body", "hashtags", "call_to_action"],
            },
        }
    },
    "required": ["variations"],
}


class GeminiTransientError(Exception):
    """Retryable failures: rate limit, timeout, temporary network, 5xx."""


class GeminiPermanentError(Exception):
    """Non-retryable failures: invalid key, bad schema, permission, bad request."""


def classify_gemini_exception(exc: Exception) -> Exception:
    message = str(exc).lower()
    permanent_markers = [
        "api key not valid",
        "invalid api key",
        "permission denied",
        "unauthenticated",
        "unsupported model",
        "model not found",
        "invalid schema",
        "invalid argument",
        "bad request",
        "400",
        "401",
        "403",
    ]
    transient_markers = [
        "429",
        "rate limit",
        "quota",
        "timeout",
        "timed out",
        "temporarily unavailable",
        "unavailable",
        "connection",
        "network",
        "500",
        "502",
        "503",
        "504",
        "deadline",
    ]
    if any(marker in message for marker in permanent_markers):
        return GeminiPermanentError(str(exc))
    if any(marker in message for marker in transient_markers):
        return GeminiTransientError(str(exc))
    return GeminiTransientError(str(exc))


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_random_exponential(multiplier=1, max=15),
    retry=retry_if_exception_type(GeminiTransientError),
)
async def _call_gemini(prompt: str, temperature: float, top_p: float) -> str:
    if not _settings.gemini_api_key:
        raise GeminiPermanentError("Gemini API key is missing. Add GEMINI_API_KEY to backend/.env before generating.")
    model = genai.GenerativeModel(_settings.gemini_model)
    try:
        result = await model.generate_content_async(
            prompt,
            generation_config=genai.GenerationConfig(
                temperature=temperature,
                top_p=top_p,
                response_mime_type="application/json",
                response_schema=_RESPONSE_SCHEMA,
            ),
        )
    except Exception as exc:
        classified = classify_gemini_exception(exc)
        if isinstance(classified, GeminiPermanentError):
            logger.error("Gemini permanent failure: %s", classified)
            raise classified from exc
        logger.warning("Gemini transient failure, retrying if attempts remain: %s", classified)
        raise classified from exc

    if not result.text:
        raise GeminiTransientError("Gemini returned an empty response. Please retry.")
    return result.text


def _normalise_payload(payload: Any) -> dict:
    if isinstance(payload, dict) and "variations" in payload:
        return payload
    if isinstance(payload, dict) and {"headline", "body", "call_to_action"}.issubset(payload.keys()):
        return {"variations": [{"style": "Safe", **payload}]}
    if isinstance(payload, list):
        return {"variations": payload}
    raise GeminiTransientError("Gemini returned JSON in an unexpected shape.")


async def generate_copy(prompt: str, temperature: float, top_p: float) -> GeneratedVariations:
    async with _semaphore:
        raw = await _call_gemini(prompt, temperature, top_p)

    try:
        payload = _normalise_payload(json.loads(raw))
    except json.JSONDecodeError as exc:
        raise GeminiTransientError(f"Gemini returned invalid JSON: {exc}") from exc

    try:
        parsed = GeneratedVariations.model_validate(payload)
    except ValidationError as exc:
        raise GeminiTransientError(f"Gemini output did not match Lexora schema: {exc}") from exc

    # Ensure useful style names if the model leaves them blank or duplicates them.
    fallback_names = ["Safe", "Creative", "Bold", "Variant 4", "Variant 5"]
    fixed: list[GeneratedCopy] = []
    used: set[str] = set()
    for index, item in enumerate(parsed.variations):
        style = item.style.strip() or fallback_names[min(index, len(fallback_names) - 1)]
        if style.lower() in used:
            style = fallback_names[min(index, len(fallback_names) - 1)]
        used.add(style.lower())
        fixed.append(item.model_copy(update={"style": style}))
    return GeneratedVariations(variations=fixed)
