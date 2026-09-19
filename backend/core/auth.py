"""
FastAPI authentication dependencies.

Usage in routes:
    from core.auth import get_current_user
    user = Depends(get_current_user)
"""

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.auth_service import get_current_user as _get_user
from models.user import User
from common.exceptions import BadRequestError


async def get_current_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Extract and validate the JWT token from the Authorization header.

    Header format: Authorization: Bearer <token>

    Returns the authenticated User or raises 400.
    """
    if not authorization:
        raise BadRequestError(
            "Missing Authorization header. Format: Authorization: Bearer <token>"
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise BadRequestError(
            "Invalid Authorization header. Format: Authorization: Bearer <token>"
        )

    return await _get_user(db, token)
