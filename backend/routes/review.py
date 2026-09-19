"""
Review routes — daily review, quiz answers, and stats (protected).
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db_session
from core.auth import get_current_user
from models.user import User
from schemas.review import (
    ReviewDueResponse,
    ReviewAnswerRequest,
    ReviewAnswerResponse,
    ReviewStatsResponse,
)
from services import review_service

router = APIRouter(prefix="/review", tags=["Review"])


@router.get("/due", response_model=ReviewDueResponse)
async def get_due_reviews(
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get words due for review right now."""
    items, total = await review_service.get_due_reviews(db, user.id, limit)
    return ReviewDueResponse(items=items, total_due=total)


@router.post("/answer", response_model=ReviewAnswerResponse)
async def submit_review_answer(
    payload: ReviewAnswerRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Submit a quiz answer and update the review schedule."""
    result = await review_service.submit_answer(db, user.id, payload)
    return result


@router.get("/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get the user's learning statistics."""
    stats = await review_service.get_review_stats(db, user.id)
    return stats
