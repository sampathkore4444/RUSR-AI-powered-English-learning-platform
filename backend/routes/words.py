"""
Word intelligence routes — tap-to-lookup and AI sentence explanation (protected).
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db_session
from core.auth import get_current_user
from models.user import User
from schemas.word import (
    WordInspectRequest,
    WordInspectResponse,
    ExplainRequest,
    ExplainResponse,
)
from services import word_intelligence_service

router = APIRouter(prefix="/words", tags=["Word Intelligence"])


@router.post("/inspect", response_model=WordInspectResponse)
async def inspect_word(
    payload: WordInspectRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Tap-to-lookup: get full word intelligence for a tapped word.

    Returns definition, POS, synonyms, context meaning, and example.
    """
    result = await word_intelligence_service.inspect_word(payload)
    return result


@router.post("/explain", response_model=ExplainResponse)
async def explain_sentence(
    payload: ExplainRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    AI explanation of a selected sentence.

    Supports: simple, grammar, vocabulary, examples, translate.
    """
    result = await word_intelligence_service.explain_sentence(payload)
    return result
