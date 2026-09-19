"""
Vocabulary service — personal word store CRUD and management.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import NotFoundError, ConflictError
from models.vocabulary import UserVocabulary
from models.learning_event import LearningEvent
from schemas.vocabulary import VocabularySave, VocabularyUpdate


async def save_word(db: AsyncSession, user_id: str, payload: VocabularySave) -> UserVocabulary:
    """
    Save a new word to the user's personal vocabulary.

    Raises ConflictError if the word is already saved.
    """
    existing = await db.execute(
        select(UserVocabulary).where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.lemma == payload.lemma.lower(),
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Word '{payload.word}' is already in your vocabulary")

    vocab = UserVocabulary(
        user_id=user_id,
        word=payload.word,
        lemma=payload.lemma.lower(),
        meaning=payload.meaning,
        difficulty=payload.difficulty,
        next_review_date=_compute_next_review(1),
    )
    db.add(vocab)
    await db.flush()

    event = LearningEvent(
        user_id=user_id,
        vocabulary_id=vocab.id,
        event_type="SAVED",
        context_sentence=payload.context_sentence,
    )
    db.add(event)
    await db.flush()

    return vocab


async def get_vocabulary(
    db: AsyncSession, user_id: str, offset: int = 0, limit: int = 50
) -> tuple[list[UserVocabulary], int]:
    """List the user's saved words with pagination."""
    count_result = await db.execute(
        select(func.count(UserVocabulary.id)).where(
            UserVocabulary.user_id == user_id
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(UserVocabulary)
        .where(UserVocabulary.user_id == user_id)
        .order_by(UserVocabulary.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    words = list(result.scalars().all())
    return words, total


async def get_vocabulary_word(db: AsyncSession, vocab_id: str) -> UserVocabulary:
    """Fetch a single saved word by ID."""
    result = await db.execute(
        select(UserVocabulary).where(UserVocabulary.id == vocab_id)
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        raise NotFoundError("Vocabulary word", vocab_id)
    return vocab


async def update_vocabulary(
    db: AsyncSession, vocab_id: str, payload: VocabularyUpdate
) -> UserVocabulary:
    """Update personal note, meaning, or difficulty of a saved word."""
    vocab = await get_vocabulary_word(db, vocab_id)

    if payload.meaning is not None:
        vocab.meaning = payload.meaning
    if payload.personal_note is not None:
        vocab.personal_note = payload.personal_note
    if payload.difficulty is not None:
        vocab.difficulty = payload.difficulty

    await db.flush()
    return vocab


async def delete_vocabulary(db: AsyncSession, vocab_id: str) -> None:
    """Remove a word from personal vocabulary."""
    vocab = await get_vocabulary_word(db, vocab_id)
    await db.delete(vocab)
    await db.flush()


async def get_word_of_day(db: AsyncSession, user_id: str) -> dict | None:
    """
    Select a "word of the day" from the user's vocabulary.

    Priority logic:
      1. Words due for review today (lowest mastery first)
      2. Words never reviewed (lowest mastery first)
      3. Any word with lowest mastery

    Returns None if the user has no saved words.
    """
    now = datetime.now(timezone.utc)

    # Priority 1: Due for review today, lowest mastery
    due_result = await db.execute(
        select(UserVocabulary)
        .where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.next_review_date <= now,
        )
        .order_by(UserVocabulary.mastery_level.asc())
        .limit(1)
    )
    vocab = due_result.scalar_one_or_none()
    if vocab:
        return _vocab_to_wod(vocab, "due_for_review")

    # Priority 2: Never reviewed, lowest mastery
    new_result = await db.execute(
        select(UserVocabulary)
        .where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.times_reviewed == 0,
        )
        .order_by(UserVocabulary.mastery_level.asc())
        .limit(1)
    )
    vocab = new_result.scalar_one_or_none()
    if vocab:
        return _vocab_to_wod(vocab, "new_word")

    # Priority 3: Lowest mastery overall
    low_result = await db.execute(
        select(UserVocabulary)
        .where(UserVocabulary.user_id == user_id)
        .order_by(UserVocabulary.mastery_level.asc())
        .limit(1)
    )
    vocab = low_result.scalar_one_or_none()
    if vocab:
        return _vocab_to_wod(vocab, "weakest_word")

    return None


def _vocab_to_wod(vocab: UserVocabulary, reason: str) -> dict:
    """Convert a vocabulary word to a word-of-the-day response."""
    return {
        "id": vocab.id,
        "word": vocab.word,
        "lemma": vocab.lemma,
        "meaning": vocab.meaning,
        "difficulty": vocab.difficulty,
        "mastery_level": vocab.mastery_level,
        "times_reviewed": vocab.times_reviewed,
        "next_review_date": vocab.next_review_date,
        "reason": reason,
    }


# ── Private helpers ──────────────────────────────────────


_REVIEW_INTERVALS = [1, 3, 7, 14, 30, 60]


def _compute_next_review(review_number: int) -> datetime:
    """Compute the next review date based on the fixed interval schedule."""
    idx = min(review_number, len(_REVIEW_INTERVALS)) - 1
    days = _REVIEW_INTERVALS[idx]
    return datetime.now(timezone.utc) + timedelta(days=days)
