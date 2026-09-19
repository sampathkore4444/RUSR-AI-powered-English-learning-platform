"""
Database initialization script.

Usage:
    python -m scripts.init_db

Creates all tables and optionally seeds initial data.
"""

import asyncio
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import engine, Base, async_session_factory
from models import *  # noqa: F401, F403
from services.auth_service import register
from schemas.user import UserCreate


async def create_tables():
    """Create all tables from ORM models."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully.")


async def seed_demo_user():
    """Create a demo user for testing."""
    async with async_session_factory() as db:
        try:
            user = await register(
                db,
                UserCreate(
                    email="demo@rusr.app",
                    password="demo1234",
                    full_name="Demo User",
                ),
            )
            await db.commit()
            print(f"✅ Demo user created: {user.email}")
        except Exception as e:
            if "already registered" in str(e):
                print("ℹ️  Demo user already exists, skipping.")
            else:
                print(f"⚠️  Could not create demo user: {e}")


async def download_nltk_data():
    """Download required NLTK data."""
    import nltk
    try:
        nltk.data.find("corpora/wordnet")
        print("ℹ️  NLTK WordNet already downloaded.")
    except LookupError:
        print("📥 Downloading NLTK WordNet...")
        nltk.download("wordnet", quiet=True)
        nltk.download("omw-1.4", quiet=True)
        print("✅ NLTK WordNet downloaded.")


async def download_spacy_model():
    """Download spaCy English model if not present."""
    try:
        import spacy
        spacy.load("en_core_web_sm")
        print("ℹ️  spaCy en_core_web_sm already installed.")
    except OSError:
        print("📥 Downloading spaCy en_core_web_sm...")
        import subprocess
        subprocess.run(
            [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
            check=True,
        )
        print("✅ spaCy model downloaded.")


async def main():
    print("🚀 Initializing database...\n")

    await download_nltk_data()
    await download_spacy_model()
    await create_tables()
    await seed_demo_user()

    print("\n🎉 Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
