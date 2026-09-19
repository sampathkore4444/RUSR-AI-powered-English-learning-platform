"""
Auth service — JWT authentication, password hashing, token management.
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from common.exceptions import BadRequestError, NotFoundError
from models.user import User
from schemas.user import UserCreate, UserResponse

settings = get_settings()

# ── Password hashing ─────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT tokens ────────────────────────────────────────────

ALGORITHM = "HS256"


def create_access_token(user_id: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token for a user."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """
    Decode and validate a JWT token.  Returns the user_id.

    Raises BadRequestError on invalid/expired tokens.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise BadRequestError("Invalid token: missing subject")
        return user_id
    except JWTError as e:
        raise BadRequestError(f"Invalid token: {e}")


# ── User operations ───────────────────────────────────────


async def register(db: AsyncSession, payload: UserCreate) -> User:
    """Register a new user.  Raises ConflictError if email exists."""
    from common.exceptions import ConflictError

    existing = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if existing.scalar_one_or_none():
        raise ConflictError(f"Email '{payload.email}' is already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    await db.flush()
    return user


async def login(db: AsyncSession, email: str, password: str) -> dict:
    """
    Authenticate a user and return a JWT token.

    Returns:
        {"access_token": str, "token_type": "bearer", "user": UserResponse}
    """
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise BadRequestError("Invalid email or password")

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.model_validate(user),
    }


async def get_current_user(db: AsyncSession, token: str) -> User:
    """Get the current authenticated user from a JWT token."""
    user_id = decode_access_token(token)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("User", user_id)
    return user
