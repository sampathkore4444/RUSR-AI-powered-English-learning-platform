"""
Redis caching layer — wraps Redis with JSON serialization and TTL support.

Used for:
  - Dictionary lookups (expensive WordNet queries)
  - AI explanations (LLM calls)
  - Session data
"""

import json
import hashlib
import logging
from typing import Any

from core.redis import redis_client

logger = logging.getLogger(__name__)

# Default TTLs (seconds)
DICTIONARY_TTL = 86400 * 7   # 7 days — definitions don't change
AI_EXPLANATION_TTL = 86400    # 1 day — explanations are somewhat stable
PRONUNCIATION_TTL = 86400 * 30 # 30 days — pronunciation never changes


def _make_key(prefix: str, *args: str) -> str:
    """Create a cache key from prefix and arguments."""
    raw = ":".join(str(a) for a in args)
    hashed = hashlib.md5(raw.encode()).hexdigest()[:12]
    return f"rusr:{prefix}:{hashed}"


async def get_cached(prefix: str, *args: str) -> Any | None:
    """Get a value from cache. Returns None on miss."""
    key = _make_key(prefix, *args)
    try:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning("Cache get failed: %s", e)
        return None


async def set_cached(prefix: str, value: Any, ttl: int, *args: str) -> None:
    """Set a value in cache with TTL."""
    key = _make_key(prefix, *args)
    try:
        await redis_client.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.warning("Cache set failed: %s", e)


async def invalidate_cached(prefix: str, *args: str) -> None:
    """Remove a value from cache."""
    key = _make_key(prefix, *args)
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning("Cache delete failed: %s", e)


# ── Convenience wrappers ─────────────────────────────────


async def cache_dictionary(word: str, data: dict) -> None:
    """Cache a dictionary lookup result."""
    await set_cached("dict", data, DICTIONARY_TTL, word)


async def get_cached_dictionary(word: str) -> dict | None:
    """Get a cached dictionary lookup."""
    return await get_cached("dict", word)


async def cache_explanation(key_parts: str, data: str) -> None:
    """Cache an AI explanation."""
    await set_cached("ai_explain", data, AI_EXPLANATION_TTL, key_parts)


async def get_cached_explanation(key_parts: str) -> str | None:
    """Get a cached AI explanation."""
    return await get_cached("ai_explain", key_parts)


async def cache_pronunciation(word: str, data: str | None) -> None:
    """Cache pronunciation data."""
    await set_cached("pron", data, PRONUNCIATION_TTL, word)


async def get_cached_pronunciation(word: str) -> str | None:
    """Get cached pronunciation."""
    return await get_cached("pron", word)
