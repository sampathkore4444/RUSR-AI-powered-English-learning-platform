"""
Learning event service — tracks all user interactions for analytics.

Events from SPEC §11:
  WORD_VIEWED, WORD_SAVED, WORD_REVIEWED,
  QUIZ_STARTED, QUIZ_ANSWERED,
  ARTICLE_READ, ARTICLE_COMPLETED,
  AI_EXPLANATION_REQUESTED
"""

from sqlalchemy.ext.asyncio import AsyncSession
from models.learning_event import LearningEvent


async def track_event(
    db: AsyncSession,
    user_id: str,
    event_type: str,
    vocabulary_id: str | None = None,
    article_id: str | None = None,
    context_sentence: str | None = None,
    metadata_json: str | None = None,
) -> LearningEvent:
    """Record a learning event."""
    event = LearningEvent(
        user_id=user_id,
        vocabulary_id=vocabulary_id,
        event_type=event_type,
        context_sentence=context_sentence,
    )
    db.add(event)
    await db.flush()
    return event


# ── Convenience functions ────────────────────────────────


async def track_word_viewed(
    db: AsyncSession, user_id: str, vocabulary_id: str, sentence: str | None = None
) -> LearningEvent:
    return await track_event(db, user_id, "WORD_VIEWED", vocabulary_id, context_sentence=sentence)


async def track_word_saved(
    db: AsyncSession, user_id: str, vocabulary_id: str, sentence: str | None = None
) -> LearningEvent:
    return await track_event(db, user_id, "WORD_SAVED", vocabulary_id, context_sentence=sentence)


async def track_article_read(
    db: AsyncSession, user_id: str, article_id: str
) -> LearningEvent:
    return await track_event(db, user_id, "ARTICLE_READ", article_id=article_id)


async def track_article_completed(
    db: AsyncSession, user_id: str, article_id: str
) -> LearningEvent:
    return await track_event(db, user_id, "ARTICLE_COMPLETED", article_id=article_id)


async def track_ai_explanation(
    db: AsyncSession, user_id: str, sentence: str, action: str
) -> LearningEvent:
    return await track_event(
        db, user_id, "AI_EXPLANATION_REQUESTED",
        context_sentence=f"[{action}] {sentence}",
    )


async def track_quiz_started(
    db: AsyncSession, user_id: str, vocabulary_id: str
) -> LearningEvent:
    return await track_event(db, user_id, "QUIZ_STARTED", vocabulary_id)
