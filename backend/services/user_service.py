"""
User service — profile operations.

Registration and authentication are handled by auth_service.
This module covers profile-related operations.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from common.exceptions import NotFoundError
from models.user import User


async def get_user_by_id(db: AsyncSession, user_id: str) -> User:
    """Fetch a user by ID.  Raises NotFoundError."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_id)
    return user


async def update_user_profile(
    db: AsyncSession, user_id: str, full_name: str | None = None
) -> User:
    """Update user profile fields."""
    user = await get_user_by_id(db, user_id)
    if full_name is not None:
        user.full_name = full_name
    await db.flush()
    return user
