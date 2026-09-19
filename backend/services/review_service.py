"""
Review service — spaced repetition, quizzes, daily review, and streak tracking.

MVP uses fixed intervals.  Evolve to FSRS later.
"""

from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import NotFoundError
from models.vocabulary import UserVocabulary
from models.learning_event import LearningEvent
from schemas.review import (
    ReviewDueItem,
    ReviewAnswerRequest,
    ReviewAnswerResponse,
    ReviewStatsResponse,
)

# Fixed interval schedule (days)
_REVIEW_INTERVALS = [1, 3, 7, 14, 30, 60]


async def get_due_reviews(
    db: AsyncSession, user_id: str, limit: int = 20
) -> tuple[list[ReviewDueItem], int]:
    """Fetch words that are due for review right now."""
    now = datetime.now(timezone.utc)

    count_result = await db.execute(
        select(func.count(UserVocabulary.id)).where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.next_review_date <= now,
        )
    )
    total_due = count_result.scalar() or 0

    result = await db.execute(
        select(UserVocabulary)
        .where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.next_review_date <= now,
        )
        .order_by(UserVocabulary.next_review_date.asc())
        .limit(limit)
    )
    words = list(result.scalars().all())

    items = [
        ReviewDueItem(
            vocabulary_id=w.id,
            word=w.word,
            lemma=w.lemma,
            meaning=w.meaning,
            difficulty=w.difficulty,
            context_sentence=None,
        )
        for w in words
    ]
    return items, total_due


async def submit_answer(
    db: AsyncSession, user_id: str, payload: ReviewAnswerRequest
) -> ReviewAnswerResponse:
    """Process a quiz answer and update mastery + schedule."""
    result = await db.execute(
        select(UserVocabulary).where(
            UserVocabulary.id == payload.vocabulary_id,
            UserVocabulary.user_id == user_id,
        )
    )
    vocab = result.scalar_one_or_none()
    if not vocab:
        raise NotFoundError("Vocabulary word", payload.vocabulary_id)

    if payload.answer_correct:
        vocab.mastery_level = min(1.0, vocab.mastery_level + 0.15)
        vocab.times_reviewed += 1
        event_type = "QUIZ_CORRECT"
    else:
        vocab.mastery_level = max(0.0, vocab.mastery_level - 0.10)
        vocab.times_reviewed += 1
        event_type = "QUIZ_WRONG"

    vocab.next_review_date = _compute_next_review(
        vocab.times_reviewed, payload.answer_correct
    )

    event = LearningEvent(
        user_id=user_id,
        vocabulary_id=vocab.id,
        event_type=event_type,
    )
    db.add(event)
    await db.flush()

    interval_idx = min(vocab.times_reviewed, len(_REVIEW_INTERVALS)) - 1
    interval_days = _REVIEW_INTERVALS[interval_idx]

    return ReviewAnswerResponse(
        vocabulary_id=vocab.id,
        correct=payload.answer_correct,
        mastery_level=vocab.mastery_level,
        next_review_date=vocab.next_review_date,
        interval_days=interval_days,
    )


async def get_review_stats(db: AsyncSession, user_id: str) -> ReviewStatsResponse:
    """Compute learning statistics including reading and quiz streaks."""
    # Total words
    total = await db.execute(
        select(func.count(UserVocabulary.id)).where(
            UserVocabulary.user_id == user_id
        )
    )
    total_words = total.scalar() or 0

    # Mastered (mastery >= 0.8)
    mastered = await db.execute(
        select(func.count(UserVocabulary.id)).where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.mastery_level >= 0.8,
        )
    )
    words_mastered = mastered.scalar() or 0

    # New (never reviewed)
    new = await db.execute(
        select(func.count(UserVocabulary.id)).where(
            UserVocabulary.user_id == user_id,
            UserVocabulary.times_reviewed == 0,
        )
    )
    words_new = new.scalar() or 0

    words_learning = total_words - words_mastered - words_new

    # Retention rate
    correct_result = await db.execute(
        select(func.count(LearningEvent.id)).where(
            LearningEvent.user_id == user_id,
            LearningEvent.event_type == "QUIZ_CORRECT",
        )
    )
    correct_count = correct_result.scalar() or 0

    total_quizzes = await db.execute(
        select(func.count(LearningEvent.id)).where(
            LearningEvent.user_id == user_id,
            LearningEvent.event_type.in_(["QUIZ_CORRECT", "QUIZ_WRONG"]),
        )
    )
    total_quiz_count = total_quizzes.scalar() or 0
    retention_rate = (
        (correct_count / total_quiz_count * 100) if total_quiz_count > 0 else 0.0
    )

    # Streaks
    reading_streak = await _calculate_streak(
        db, user_id, ["ARTICLE_READ", "ARTICLE_COMPLETED", "WORD_SAVED", "WORD_VIEWED"]
    )
    quiz_streak = await _calculate_streak(
        db, user_id, ["QUIZ_CORRECT", "QUIZ_WRONG"]
    )
    # Combined streak (any learning activity)
    combined_streak = await _calculate_streak(
        db,
        user_id,
        [
            "ARTICLE_READ",
            "ARTICLE_COMPLETED",
            "WORD_SAVED",
            "WORD_VIEWED",
            "QUIZ_CORRECT",
            "QUIZ_WRONG",
            "AI_EXPLANATION_REQUESTED",
        ],
    )

    return ReviewStatsResponse(
        total_words=total_words,
        words_mastered=words_mastered,
        words_learning=words_learning,
        words_new=words_new,
        retention_rate=round(retention_rate, 1),
        streak_days=combined_streak,
        reading_streak_days=reading_streak,
        quiz_streak_days=quiz_streak,
    )


# ── Private helpers ──────────────────────────────────────


_REVIEW_INTERVALS = [1, 3, 7, 14, 30, 60]


def _compute_next_review(review_number: int, correct: bool) -> datetime:
    """Compute next review date."""
    now = datetime.now(timezone.utc)
    if correct:
        idx = min(review_number, len(_REVIEW_INTERVALS)) - 1
    else:
        idx = 0
    days = _REVIEW_INTERVALS[idx]
    return now + timedelta(days=days)


async def _calculate_streak(
    db: AsyncSession, user_id: str, event_types: list[str]
) -> int:
    """
    Calculate a streak for given event types.

    Counts consecutive days (backwards from today) where at least one
    matching event occurred.
    """
    now = datetime.now(timezone.utc)
    streak = 0
    current_date = now.date()

    for i in range(365):  # max 1 year streak
        day_start = datetime(
            current_date.year, current_date.month, current_date.day,
            tzinfo=timezone.utc,
        )
        day_end = day_start + timedelta(days=1)

        result = await db.execute(
            select(func.count(LearningEvent.id)).where(
                LearningEvent.user_id == user_id,
                LearningEvent.event_type.in_(event_types),
                LearningEvent.created_at >= day_start,
                LearningEvent.created_at < day_end,
            )
        )
        count = result.scalar() or 0

        if count > 0:
            streak += 1
            current_date -= timedelta(days=1)
        else:
            # Allow today to be empty if it's early (no activity yet today)
            if i == 0:
                current_date -= timedelta(days=1)
                continue
            break

    return streak
