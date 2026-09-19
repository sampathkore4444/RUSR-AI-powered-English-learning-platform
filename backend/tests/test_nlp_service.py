"""
Tests for nlp_service — tokenization, POS tagging, lemmatization, sentence splitting.
"""

import pytest
from services.nlp_service import (
    process_sentence,
    split_sentences,
    get_lemma,
    get_pos,
)


@pytest.mark.asyncio
class TestProcessSentence:
    async def test_returns_tokens(self):
        tokens = await process_sentence("The cat sat on the mat.")
        assert len(tokens) > 0
        assert all("text" in t for t in tokens)
        assert all("lemma" in t for t in tokens)
        assert all("pos" in t for t in tokens)

    async def test_tokenize_simple_sentence(self):
        tokens = await process_sentence("Hello world")
        texts = [t["text"] for t in tokens]
        assert "Hello" in texts
        assert "world" in texts

    async def test_lemmatization(self):
        tokens = await process_sentence("The cats were running")
        # "cats" → "cat", "were" → "be", "running" → "run"
        lemmas = [t["lemma"].lower() for t in tokens]
        assert "cat" in lemmas
        assert "run" in lemmas

    async def test_pos_tags(self):
        tokens = await process_sentence("She runs quickly")
        pos_tags = [t["pos"] for t in tokens]
        assert "VERB" in pos_tags or "AUX" in pos_tags

    async def test_empty_string(self):
        tokens = await process_sentence("")
        assert tokens == []


@pytest.mark.asyncio
class TestSplitSentences:
    async def test_splits_on_periods(self):
        sentences = await split_sentences("First sentence. Second sentence.")
        assert len(sentences) == 2

    async def test_splits_on_multiple_punctuation(self):
        sentences = await split_sentences("Hello! How are you? I'm fine.")
        assert len(sentences) == 3

    async def test_handles_single_sentence(self):
        sentences = await split_sentences("Just one sentence")
        assert len(sentences) == 1

    async def test_handles_empty_string(self):
        sentences = await split_sentences("")
        assert len(sentences) == 0

    async def test_complex_paragraph(self):
        text = (
            "The Federal Reserve raised interest rates by 25 basis points. "
            "This marks the tenth consecutive increase. "
            "Chair Powell signaled a pause in future hikes."
        )
        sentences = await split_sentences(text)
        assert len(sentences) == 3


@pytest.mark.asyncio
class TestGetLemma:
    async def test_lemma_of_regular_noun(self):
        lemma = await get_lemma("cats")
        assert lemma == "cat"

    async def test_lemma_of_verb(self):
        lemma = await get_lemma("running")
        assert lemma == "run"

    async def test_lemma_of_single_word(self):
        lemma = await get_lemma("hello")
        assert lemma == "hello"

    async def test_lemma_case_insensitive(self):
        lemma = await get_lemma("Running")
        assert lemma.lower() == "run"


@pytest.mark.asyncio
class TestGetPos:
    async def test_pos_of_noun(self):
        pos = await get_pos("dog")
        assert pos in ("NOUN", "PROPN")

    async def test_pos_of_verb(self):
        pos = await get_pos("run")
        # "run" can be noun or verb depending on context
        assert pos in ("VERB", "NOUN")

    async def test_pos_returns_string(self):
        pos = await get_pos("hello")
        assert isinstance(pos, str)
