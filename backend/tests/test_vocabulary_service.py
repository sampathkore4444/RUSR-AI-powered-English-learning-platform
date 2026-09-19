"""
Tests for vocabulary_service — CRUD, word of the day, deduplication.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.vocabulary_service import (
    save_word,
    get_vocabulary,
    get_vocabulary_word,
    update_vocabulary,
    delete_vocabulary,
    get_word_of_day,
)
from schemas.vocabulary import VocabularySave, VocabularyUpdate
from common.exceptions import NotFoundError, ConflictError


# ── Helpers ─────────────────────────────────────────────


async def _create_test_user(db: AsyncSession) -> str:
    """Create a test user and return the user_id."""
    from services.auth_service import register
    from schemas.user import UserCreate

    user = await register(
        db,
        UserCreate(email="vocab-test@example.com", password="test123"),
    )
    return user.id


async def _save_test_word(db: AsyncSession, user_id: str, word: str = "test") -> dict:
    """Save a test word and return the result."""
    payload = VocabularySave(
        word=word,
        lemma=word.lower(),
        meaning=f"Definition of {word}",
        difficulty="Medium",
    )
    return await save_word(db, user_id, payload)


# ── Save word ───────────────────────────────────────────


@pytest.mark.asyncio
class TestSaveWord:
    async def test_save_new_word(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab = await _save_test_word(db_session, user_id, "curb")

        assert vocab.word == "curb"
        assert vocab.lemma == "curb"
        assert vocab.meaning == "Definition of curb"
        assert vocab.mastery_level == 0.0
        assert vocab.times_reviewed == 0

    async def test_save_duplicate_raises(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        await _save_test_word(db_session, user_id, "curb")

        with pytest.raises(ConflictError):
            await _save_test_word(db_session, user_id, "curb")

    async def test_save_different_words(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        await _save_test_word(db_session, user_id, "curb")
        await _save_test_word(db_session, user_id, "inflation")

        words, total = await get_vocabulary(db_session, user_id)
        assert total == 2


# ── List vocabulary ─────────────────────────────────────


@pytest.mark.asyncio
class TestListVocabulary:
    async def test_list_empty(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        words, total = await get_vocabulary(db_session, user_id)
        assert total == 0
        assert words == []

    async def test_list_with_pagination(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        for i in range(5):
            await _save_test_word(db_session, user_id, f"word{i}")

        words, total = await get_vocabulary(db_session, user_id, offset=0, limit=3)
        assert total == 5
        assert len(words) == 3


# ── Get single word ────────────────────────────────────


@pytest.mark.asyncio
class TestGetWord:
    async def test_get_existing_word(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab = await _save_test_word(db_session, user_id, "test")

        fetched = await get_vocabulary_word(db_session, vocab.id)
        assert fetched.word == "test"

    async def test_get_nonexistent_raises(self, db_session: AsyncSession):
        with pytest.raises(NotFoundError):
            await get_vocabulary_word(db_session, "nonexistent-id")


# ── Update word ────────────────────────────────────────


@pytest.mark.asyncio
class TestUpdateWord:
    async def test_update_meaning(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab = await _save_test_word(db_session, user_id, "test")

        updated = await update_vocabulary(
            db_session,
            vocab.id,
            VocabularyUpdate(meaning="New meaning"),
        )
        assert updated.meaning == "New meaning"

    async def test_update_difficulty(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab = await _save_test_word(db_session, user_id, "test")

        updated = await update_vocabulary(
            db_session,
            vocab.id,
            VocabularyUpdate(difficulty="Hard"),
        )
        assert updated.difficulty == "Hard"

    async def test_update_personal_note(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab = await _save_test_word(db_session, user_id, "test")

        updated = await update_vocabulary(
            db_session,
            vocab.id,
            VocabularyUpdate(personal_note="My note"),
        )
        assert updated.personal_note == "My note"


# ── Delete word ────────────────────────────────────────


@pytest.mark.asyncio
class TestDeleteWord:
    async def test_delete_word(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab = await _save_test_word(db_session, user_id, "test")

        await delete_vocabulary(db_session, vocab.id)

        with pytest.raises(NotFoundError):
            await get_vocabulary_word(db_session, vocab.id)

    async def test_delete_nonexistent_raises(self, db_session: AsyncSession):
        with pytest.raises(NotFoundError):
            await delete_vocabulary(db_session, "nonexistent-id")


# ── Word of the day ────────────────────────────────────


@pytest.mark.asyncio
class TestWordOfDay:
    async def test_returns_none_when_no_words(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        result = await get_word_of_day(db_session, user_id)
        assert result is None

    async def test_returns_word_with_lowest_mastery(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        await _save_test_word(db_session, user_id, "easy")
        await _save_test_word(db_session, user_id, "hard")

        result = await get_word_of_day(db_session, user_id)
        assert result is not None
        assert "word" in result
        assert "meaning" in result
        assert "mastery_level" in result

    async def test_returns_due_word_first(self, db_session: AsyncSession):
        from datetime import datetime, timezone, timedelta
        from models.vocabulary import UserVocabulary

        user_id = await _create_test_user(db_session)
        # Save two words
        easy = await _save_test_word(db_session, user_id, "easy")
        hard = await _save_test_word(db_session, user_id, "hard")

        # Make "hard" due for review (set next_review_date to past)
        hard_vocab = await get_vocabulary_word(db_session, hard.id)
        hard_vocab.next_review_date = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.flush()

        result = await get_word_of_day(db_session, user_id)
        assert result is not None
        assert result["word"] == "hard"
