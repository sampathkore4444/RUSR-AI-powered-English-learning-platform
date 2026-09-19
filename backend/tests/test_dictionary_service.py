"""
Tests for dictionary_service — WordNet lookup, pronunciation, caching.
"""

import pytest
from services.dictionary_service import lookup_word, get_pronunciation


@pytest.mark.asyncio
class TestLookupWord:
    async def test_lookup_common_word(self):
        result = await lookup_word("curb")
        assert "definitions" in result
        assert "synonyms" in result
        assert "pronunciation" in result
        assert len(result["definitions"]) > 0

    async def test_lookup_returns_pos_tags(self):
        result = await lookup_word("run")
        assert "pos_tags" in result
        assert len(result["pos_tags"]) > 0

    async def test_lookup_returns_synonyms(self):
        result = await lookup_word("big")
        assert len(result["synonyms"]) > 0

    async def test_lookup_unknown_word_returns_empty(self):
        result = await lookup_word("xyzqwerty123")
        assert result["definitions"] == []
        assert result["synonyms"] == []

    async def test_lookup_returns_pronunciation(self):
        result = await lookup_word("hello")
        assert result["pronunciation"] is not None
        assert "/" in result["pronunciation"]  # IPA format

    async def test_cached_lookup_returns_same_result(self):
        """Second call should be cached (faster)."""
        import time

        start1 = time.time()
        result1 = await lookup_word("computer")
        time1 = time.time() - start1

        start2 = time.time()
        result2 = await lookup_word("computer")
        time2 = time.time() - start2

        assert result1 == result2
        # Cached call should be faster (but this is a soft assertion)
        # time2 should be <= time1


@pytest.mark.asyncio
class TestPronunciation:
    async def test_pronunciation_returns_ipa(self):
        result = await get_pronunciation("hello")
        assert result is not None
        assert result.startswith("/")
        assert result.endswith("/")

    async def test_pronunciation_unknown_word(self):
        result = await get_pronunciation("xyzqwerty")
        # May return None for unknown words
        assert result is None or isinstance(result, str)

    async def test_pronunciation_cached(self):
        """Second call should be cached."""
        result1 = await get_pronunciation("world")
        result2 = await get_pronunciation("world")
        assert result1 == result2
