"""
Auth routes — registration and login.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db_session
from schemas.user import UserCreate, UserLogin, TokenResponse
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """Register a new user and return a JWT token."""
    user = await auth_service.register(db, payload)
    from services.auth_service import create_access_token
    token = create_access_token(user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db_session),
):
    """Login with email and password, return a JWT token."""
    result = await auth_service.login(db, payload.email, payload.password)
    return result
