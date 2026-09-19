"""
Tests for auth_service — registration, login, JWT, password hashing.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    register,
    login,
)
from schemas.user import UserCreate, UserLogin
from common.exceptions import BadRequestError


# ── Password hashing ────────────────────────────────────


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("mypassword")
        assert isinstance(hashed, str)
        assert hashed != "mypassword"

    def test_verify_password_correct(self):
        hashed = hash_password("mypassword")
        assert verify_password("mypassword", hashed) is True

    def test_verify_password_incorrect(self):
        hashed = hash_password("mypassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_produces_different_hashes(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2  # bcrypt uses random salt


# ── JWT tokens ──────────────────────────────────────────


class TestJWT:
    def test_create_and_decode_token(self):
        token = create_access_token("user-123")
        user_id = decode_access_token(token)
        assert user_id == "user-123"

    def test_decode_invalid_token(self):
        with pytest.raises(BadRequestError):
            decode_access_token("invalid.token.here")

    def test_decode_empty_token(self):
        with pytest.raises(BadRequestError):
            decode_access_token("")

    def test_token_contains_user_id(self):
        token = create_access_token("user-456")
        decoded = decode_access_token(token)
        assert decoded == "user-456"


# ── Registration ────────────────────────────────────────


@pytest.mark.asyncio
class TestRegister:
    async def test_register_new_user(self, db_session: AsyncSession):
        payload = UserCreate(
            email="new@example.com",
            password="password123",
            full_name="New User",
        )
        user = await register(db_session, payload)
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.id is not None

    async def test_register_duplicate_email_raises(self, db_session: AsyncSession):
        from common.exceptions import ConflictError

        payload = UserCreate(
            email="dup@example.com",
            password="password123",
        )
        await register(db_session, payload)

        with pytest.raises(ConflictError):
            await register(db_session, payload)

    async def test_register_stores_hashed_password(self, db_session: AsyncSession):
        payload = UserCreate(
            email="hash@example.com",
            password="mypassword",
        )
        user = await register(db_session, payload)
        assert user.hashed_password != "mypassword"
        assert verify_password("mypassword", user.hashed_password)


# ── Login ───────────────────────────────────────────────


@pytest.mark.asyncio
class TestLogin:
    async def test_login_returns_token(self, db_session: AsyncSession):
        # Register first
        payload = UserCreate(
            email="login@example.com",
            password="password123",
        )
        await register(db_session, payload)

        # Login
        result = await login(db_session, "login@example.com", "password123")
        assert "access_token" in result
        assert result["token_type"] == "bearer"
        assert result["user"].email == "login@example.com"

    async def test_login_wrong_password_raises(self, db_session: AsyncSession):
        payload = UserCreate(
            email="wrong@example.com",
            password="password123",
        )
        await register(db_session, payload)

        with pytest.raises(BadRequestError):
            await login(db_session, "wrong@example.com", "wrongpassword")

    async def test_login_nonexistent_user_raises(self, db_session: AsyncSession):
        with pytest.raises(BadRequestError):
            await login(db_session, "nobody@example.com", "password")
