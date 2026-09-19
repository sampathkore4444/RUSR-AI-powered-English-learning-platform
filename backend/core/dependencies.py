"""
Reusable FastAPI dependencies.

These are injected into route handlers via `Depends(...)`.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db


# Re-export for convenience so routes can write:
#   from core.dependencies import get_db_session
get_db_session = get_db
