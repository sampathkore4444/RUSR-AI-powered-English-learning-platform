"""
Vocabulary schemas — request/response models for personal vocabulary CRUD.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class VocabularySave(BaseModel):
    """Request to save a new word."""
    word: str = Field(..., min_length=1, max_length=100)
    lemma: str = Field(..., min_length=1, max_length=100)
    meaning: str | None = None
    context_sentence: str | None = None
    difficulty: str = Field(default="Medium", pattern=r"^(Easy|Medium|Hard)$")


class VocabularyUpdate(BaseModel):
    """Request to update a saved word."""
    meaning: str | None = None
    personal_note: str | None = None
    difficulty: str | None = Field(default=None, pattern=r"^(Easy|Medium|Hard)$")


class VocabularyResponse(BaseModel):
    """Response for a single vocabulary word."""
    id: str
    word: str
    lemma: str
    meaning: str | None
    first_seen: datetime
    times_seen: int
    times_reviewed: int
    mastery_level: float
    difficulty: str
    personal_note: str | None
    next_review_date: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class VocabularyListResponse(BaseModel):
    """Response for vocabulary list."""
    vocabulary: list[VocabularyResponse]
    total: int


class WordOfDayResponse(BaseModel):
    """Response for word of the day — selected from user's vocabulary."""
    id: str
    word: str
    lemma: str
    meaning: str | None
    difficulty: str
    mastery_level: float
    times_reviewed: int
    next_review_date: datetime | None
    context_sentence: str | None = None
