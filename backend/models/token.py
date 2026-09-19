"""
SentenceToken — each word within a sentence, annotated by NLP.
"""

import uuid

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class SentenceToken(Base):
    __tablename__ = "sentence_tokens"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    sentence_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article_sentences.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(255))       # surface form: "curbed"
    lemma: Mapped[str] = mapped_column(String(255))      # base form: "curb"
    pos: Mapped[str] = mapped_column(String(50))         # part of speech: VERB

    # Relationships
    sentence = relationship("ArticleSentence", back_populates="tokens")
