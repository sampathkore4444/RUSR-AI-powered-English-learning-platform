"""
Article schemas.
"""

from datetime import datetime
from pydantic import BaseModel


class ArticleCreateFromURL(BaseModel):
    """Request body: ingest article from a URL."""
    url: str


class ArticleCreate(BaseModel):
    """Request body: ingest article from pasted text."""
    title: str
    text: str
    source: str | None = None
    author: str | None = None


class TokenResponse(BaseModel):
    text: str
    lemma: str
    pos: str

    model_config = {"from_attributes": True}


class SentenceResponse(BaseModel):
    id: str
    sequence: int
    text: str
    tokens: list[TokenResponse] = []

    model_config = {"from_attributes": True}


class ParagraphResponse(BaseModel):
    id: str
    sequence: int
    text: str
    sentences: list[SentenceResponse] = []

    model_config = {"from_attributes": True}


class ArticleResponse(BaseModel):
    id: str
    title: str
    source: str | None
    url: str | None
    author: str | None
    published_at: datetime | None
    created_at: datetime
    paragraphs: list[ParagraphResponse] = []

    model_config = {"from_attributes": True}


class ArticleListResponse(BaseModel):
    articles: list[ArticleResponse]
    total: int
