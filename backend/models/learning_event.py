"""
LearningEvent — tracks every study interaction for spaced repetition.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class LearningEvent(Base):
    __tablename__ = "learning_events"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    vocabulary_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("user_vocabulary.id", ondelete="CASCADE"),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(50)
    )  # DISCOVERED, SAVED, REVIEWED, QUIZ_CORRECT, QUIZ_WRONG
    context_sentence: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    vocabulary = relationship("UserVocabulary", back_populates="events")
