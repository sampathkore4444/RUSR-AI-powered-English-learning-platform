"""
Article-related models: Article, ArticleParagraph, ArticleSentence.
"""

import uuid
from datetime import datetime

from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(500))
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="articles")
    paragraphs = relationship(
        "ArticleParagraph",
        back_populates="article",
        lazy="selectin",
        order_by="ArticleParagraph.sequence",
    )


class ArticleParagraph(Base):
    __tablename__ = "article_paragraphs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    article_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("articles.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    # Relationships
    article = relationship("Article", back_populates="paragraphs")
    sentences = relationship(
        "ArticleSentence",
        back_populates="paragraph",
        lazy="selectin",
        order_by="ArticleSentence.sequence",
    )


class ArticleSentence(Base):
    __tablename__ = "article_sentences"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    paragraph_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("article_paragraphs.id", ondelete="CASCADE"), index=True
    )
    sequence: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    # Relationships
    paragraph = relationship("ArticleParagraph", back_populates="sentences")
    tokens = relationship(
        "SentenceToken",
        back_populates="sentence",
        lazy="selectin",
        order_by="SentenceToken.position",
    )
