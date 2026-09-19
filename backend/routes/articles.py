"""
Article routes — ingestion, listing, and retrieval (protected).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db_session
from core.auth import get_current_user
from models.user import User
from schemas.article import (
    ArticleCreate,
    ArticleCreateFromURL,
    ArticleResponse,
    ArticleListResponse,
)
from services import article_service

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("/url", response_model=ArticleResponse, status_code=201)
async def ingest_from_url(
    payload: ArticleCreateFromURL,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Ingest an article by pasting a URL."""
    article = await article_service.ingest_from_url(db, user.id, payload)
    return article


@router.post("/text", response_model=ArticleResponse, status_code=201)
async def ingest_from_text(
    payload: ArticleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Ingest an article by pasting text."""
    article = await article_service.ingest_from_text(db, user.id, payload)
    return article


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List the user's articles."""
    articles, total = await article_service.list_articles(db, user.id, offset, limit)
    return ArticleListResponse(articles=articles, total=total)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a full article with paragraphs, sentences, and tokens."""
    article = await article_service.get_article(db, article_id)
    return article
