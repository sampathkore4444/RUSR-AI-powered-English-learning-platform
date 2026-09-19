"""
SentenceEmbedding — stores vector embeddings for semantic search.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from core.database import Base


class SentenceEmbedding(Base):
    __tablename__ = "sentence_embeddings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    sentence_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("article_sentences.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(384))  # 384-dim for MiniLM-L6
    model_name: Mapped[str] = mapped_column(String(100), default="all-MiniLM-L6-v2")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
