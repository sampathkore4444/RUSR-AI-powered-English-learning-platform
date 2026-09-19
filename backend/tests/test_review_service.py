"""
Tests for review_service — due reviews, quiz answers, stats, streak.
"""

import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from services.review_service import (
    get_due_reviews,
    submit_answer,
    get_review_stats,
)
from services.vocabulary_service import save_word, get_vocabulary_word
from schemas.vocabulary import VocabularySave
from schemas.review import ReviewAnswerRequest


# ── Helpers ─────────────────────────────────────────────


async def _create_test_user(db: AsyncSession) -> str:
    from services.auth_service import register
    from schemas.user import UserCreate

    user = await register(
        db,
        UserCreate(email="review-test@example.com", password="test123"),
    )
    return user.id


async def _save_and_make_due(db: AsyncSession, user_id: str, word: str = "curb") -> str:
    """Save a word and make it due for review. Returns vocab_id."""
    vocab = await save_word(
        db,
        user_id,
        VocabularySave(word=word, lemma=word.lower(), meaning=f"Meaning of {word}"),
    )
    # Make it due for review
    vocab_obj = await get_vocabulary_word(db, vocab.id)
    vocab_obj.next_review_date = datetime.now(timezone.utc) - timedelta(days=1)
    await db.flush()
    return vocab.id


# ── Due reviews ────────────────────────────────────────


@pytest.mark.asyncio
class TestDueReviews:
    async def test_returns_empty_when_no_words(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        items, total = await get_due_reviews(db_session, user_id)
        assert total == 0
        assert items == []

    async def test_returns_due_words(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        await _save_and_make_due(db_session, user_id, "curb")
        await _save_and_make_due(db_session, user_id, "inflation")

        items, total = await get_due_reviews(db_session, user_id)
        assert total == 2
        assert len(items) == 2

    async def test_respects_limit(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        for i in range(5):
            await _save_and_make_due(db_session, user_id, f"word{i}")

        items, total = await get_due_reviews(db_session, user_id, limit=3)
        assert total == 5
        assert len(items) == 3

    async def test_excludes_future_words(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        # Save a word that's NOT due (future review date)
        vocab = await save_word(
            db_session,
            user_id,
            VocabularySave(word="future", lemma="future", meaning="Not due yet"),
        )
        items, total = await get_due_reviews(db_session, user_id)
        assert total == 0


# ── Submit answer ──────────────────────────────────────


@pytest.mark.asyncio
class TestSubmitAnswer:
    async def test_correct_answer_increases_mastery(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab_id = await _save_and_make_due(db_session, user_id)

        vocab_before = await get_vocabulary_word(db_session, vocab_id)
        mastery_before = vocab_before.mastery_level

        result = await submit_answer(
            db_session,
            user_id,
            ReviewAnswerRequest(vocabulary_id=vocab_id, answer_correct=True),
        )

        assert result.correct is True
        assert result.mastery_level > mastery_before

    async def test_wrong_answer_decreases_mastery(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab_id = await _save_and_make_due(db_session, user_id)

        # First give correct answer to raise mastery
        await submit_answer(
            db_session,
            user_id,
            ReviewAnswerRequest(vocabulary_id=vocab_id, answer_correct=True),
        )
        vocab = await get_vocabulary_word(db_session, vocab_id)
        mastery_after_correct = vocab.mastery_level

        # Now answer wrong
        await submit_answer(
            db_session,
            user_id,
            ReviewAnswerRequest(vocabulary_id=vocab_id, answer_correct=False),
        )
        vocab = await get_vocabulary_word(db_session, vocab_id)
        assert vocab.mastery_level < mastery_after_correct

    async def test_increments_times_reviewed(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab_id = await _save_and_make_due(db_session, user_id)

        await submit_answer(
            db_session,
            user_id,
            ReviewAnswerRequest(vocabulary_id=vocab_id, answer_correct=True),
        )

        vocab = await get_vocabulary_word(db_session, vocab_id)
        assert vocab.times_reviewed == 1

    async def test_nonexistent_word_raises(self, db_session: AsyncSession):
        from common.exceptions import NotFoundError

        user_id = await _create_test_user(db_session)
        with pytest.raises(NotFoundError):
            await submit_answer(
                db_session,
                user_id,
                ReviewAnswerRequest(vocabulary_id="fake-id", answer_correct=True),
            )


# ── Review stats ───────────────────────────────────────


@pytest.mark.asyncio
class TestReviewStats:
    async def test_empty_stats(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        stats = await get_review_stats(db_session, user_id)

        assert stats.total_words == 0
        assert stats.words_mastered == 0
        assert stats.words_learning == 0
        assert stats.words_new == 0
        assert stats.retention_rate == 0.0
        assert stats.streak_days == 0

    async def test_stats_after_saving_words(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        await save_word(
            db_session,
            user_id,
            VocabularySave(word="word1", lemma="word1", meaning="m1"),
        )
        await save_word(
            db_session,
            user_id,
            VocabularySave(word="word2", lemma="word2", meaning="m2"),
        )

        stats = await get_review_stats(db_session, user_id)
        assert stats.total_words == 2
        assert stats.words_new == 2

    async def test_retention_rate_calculation(self, db_session: AsyncSession):
        user_id = await _create_test_user(db_session)
        vocab_id = await _save_and_make_due(db_session, user_id)

        # Answer correctly 3 times
        for _ in range(3):
            await submit_answer(
                db_session,
                user_id,
                ReviewAnswerRequest(vocabulary_id=vocab_id, answer_correct=True),
            )

        stats = await get_review_stats(db_session, user_id)
        assert stats.retention_rate == 100.0  # 100% correct
