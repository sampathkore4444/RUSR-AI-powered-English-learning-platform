"""
AI Orchestrator service — routes tasks to Ollama with retries, fallbacks, and caching.

Includes:
  - Redis caching for AI explanations (same sentence = cached response)
  - Connection health checks
  - Automatic retries with backoff
  - Graceful degradation
"""

import json
import asyncio
import logging

import httpx

from core.config import get_settings
from common.exceptions import AIServiceError
from core.cache import cache_explanation, get_cached_explanation

settings = get_settings()
logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────

MAX_RETRIES = 2
RETRY_DELAY = 1.0
REQUEST_TIMEOUT = 30.0


# ── Health check ─────────────────────────────────────────


async def check_ollama_health() -> bool:
    """Check if Ollama is running and responsive."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            return response.status_code == 200
    except (httpx.HTTPError, httpx.ConnectError):
        return False


async def ensure_model_available(model: str | None = None) -> bool:
    """Check if the required model is pulled in Ollama."""
    model = model or settings.OLLAMA_MODEL
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m.get("name", "") for m in data.get("models", [])]
                return any(model in m for m in models)
            return False
    except (httpx.HTTPError, httpx.ConnectError):
        return False


# ── Core LLM call with retries ───────────────────────────


async def _call_llm(prompt: str, model: str | None = None) -> str:
    """Call Ollama API with retries and timeout handling."""
    model = model or settings.OLLAMA_MODEL
    url = f"{settings.OLLAMA_BASE_URL}/api/generate"

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    url,
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.7, "top_p": 0.9},
                    },
                )
                response.raise_for_status()
                data = response.json()
                result = data.get("response", "").strip()

                if not result:
                    raise AIServiceError("LLM returned empty response")

                return result

        except httpx.ConnectError:
            last_error = "Cannot connect to Ollama. Is it running?"
            logger.warning("Ollama connection failed (attempt %d/%d)", attempt + 1, MAX_RETRIES + 1)
        except httpx.ReadTimeout:
            last_error = "Ollama request timed out"
            logger.warning("Ollama timeout (attempt %d/%d)", attempt + 1, MAX_RETRIES + 1)
        except httpx.HTTPStatusError as e:
            last_error = f"Ollama HTTP error: {e.response.status_code}"
            logger.warning("Ollama HTTP %d (attempt %d/%d)", e.response.status_code, attempt + 1, MAX_RETRIES + 1)
        except AIServiceError:
            raise
        except Exception as e:
            last_error = str(e)
            logger.warning("Unexpected error: %s", e)

        if attempt < MAX_RETRIES:
            await asyncio.sleep(RETRY_DELAY * (attempt + 1))

    raise AIServiceError(f"AI service unavailable after {MAX_RETRIES + 1} attempts: {last_error}")


# ── Cached LLM call ──────────────────────────────────────


async def _call_llm_cached(cache_key: str, prompt: str, model: str | None = None) -> str:
    """Call LLM with Redis caching — same prompt returns cached result."""
    cached = await get_cached_explanation(cache_key)
    if cached:
        return cached

    result = await _call_llm(prompt, model)
    await cache_explanation(cache_key, result)
    return result


# ── Public API ───────────────────────────────────────────


async def generate_explanation(sentence: str, action: str = "simple") -> str:
    """Generate an AI explanation for a sentence (cached)."""
    prompt = _build_explanation_prompt(sentence, action)
    cache_key = f"explain:{action}:{sentence[:100]}"
    return await _call_llm_cached(cache_key, prompt)


async def generate_context_meaning(word: str, sentence: str) -> str:
    """Explain what a word means in context (cached)."""
    prompt = (
        f"You are an English teacher. A student is reading this sentence:\n\n"
        f'"{sentence}"\n\n'
        f'They tapped the word "{word}".\n\n'
        f"In ONE short sentence, explain what '{word}' means in this specific context. "
        f"Use simple English."
    )
    cache_key = f"context:{word}:{sentence[:100]}"
    try:
        return await _call_llm_cached(cache_key, prompt)
    except AIServiceError:
        logger.warning("LLM unavailable for context meaning, using fallback")
        return f"Look up '{word}' in the dictionary for its meaning in this context."


async def generate_example(word: str, meaning: str) -> str:
    """Generate one example sentence (cached)."""
    prompt = (
        f"Generate one natural English sentence using the word '{word}' "
        f"with the meaning: {meaning}. "
        f"Return ONLY the sentence, nothing else."
    )
    cache_key = f"example:{word}:{meaning[:50]}"
    try:
        return await _call_llm_cached(cache_key, prompt)
    except AIServiceError:
        return f"The teacher will help curb the students' behavior."


async def generate_word_usage(word: str, sentence: str) -> str:
    """Explain why a specific word is used in a sentence (cached)."""
    prompt = (
        f"You are an English teacher. A student asks:\n"
        f'Why is the word "{word}" used in this sentence?\n\n'
        f'"{sentence}"\n\n'
        f"Explain the author's word choice in 2-3 sentences. "
        f"Cover connotation, register, or nuance if relevant."
    )
    cache_key = f"usage:{word}:{sentence[:100]}"
    try:
        return await _call_llm_cached(cache_key, prompt)
    except AIServiceError:
        return f"The word '{word}' was chosen for its specific meaning in this context."


async def generate_quiz(word: str, meaning: str) -> dict:
    """Generate a multiple-choice quiz question (cached)."""
    prompt = (
        f"Generate a multiple-choice vocabulary quiz question.\n"
        f"Word: '{word}'\n"
        f"Meaning: {meaning}\n\n"
        f"Return JSON with keys: question, options (array of 4 strings), correct_index (0-3).\n"
        f"Make the wrong options plausible but clearly incorrect."
    )

    cache_key = f"quiz:{word}:{meaning[:50]}"
    try:
        response = await _call_llm_cached(cache_key, prompt)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0]
        return json.loads(json_str.strip())
    except (AIServiceError, json.JSONDecodeError, IndexError) as e:
        logger.warning("Quiz generation failed, using fallback: %s", e)
        return {
            "question": f"What does '{word}' mean?",
            "options": [meaning, "unknown option", "unknown option", "unknown option"],
            "correct_index": 0,
        }


# ── Prompt builders ──────────────────────────────────────


def _build_explanation_prompt(sentence: str, action: str) -> str:
    """Build the appropriate prompt based on the requested action."""
    prompts = {
        "simple": (
            f"Rewrite this sentence in simpler English that a B1 learner would understand:\n\n"
            f'"{sentence}"'
        ),
        "grammar": (
            f"Explain the grammar of this sentence step by step:\n\n"
            f'"{sentence}"'
        ),
        "vocabulary": (
            f"Define the key vocabulary words and phrases in this sentence:\n\n"
            f'"{sentence}"'
        ),
        "usage": (
            f"Explain why each key word was chosen in this sentence. "
            f"Cover connotation, register, and nuance:\n\n"
            f'"{sentence}"'
        ),
        "examples": (
            f"Generate 3 example sentences that use similar vocabulary and structure to:\n\n"
            f'"{sentence}"'
        ),
        "translate": (
            f"Translate this sentence to simple English:\n\n"
            f'"{sentence}"'
        ),
    }
    return prompts.get(action, prompts["simple"])
