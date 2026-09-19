"""
Review and quiz schemas.
"""

from datetime import datetime
from pydantic import BaseModel


class ReviewDueItem(BaseModel):
    vocabulary_id: str
    word: str
    lemma: str
    meaning: str | None
    difficulty: str
    context_sentence: str | None = None


class ReviewDueResponse(BaseModel):
    items: list[ReviewDueItem]
    total_due: int


class ReviewAnswerRequest(BaseModel):
    """Request body: submit a quiz answer."""
    vocabulary_id: str
    answer_correct: bool
    response_time_ms: int | None = None


class ReviewAnswerResponse(BaseModel):
    vocabulary_id: str
    correct: bool
    mastery_level: float
    next_review_date: datetime
    interval_days: int


class ReviewStatsResponse(BaseModel):
    total_words: int
    words_mastered: int
    words_learning: int
    words_new: int
    retention_rate: float
    streak_days: int  # combined streak (any activity)
    reading_streak_days: int = 0
    quiz_streak_days: int = 0
