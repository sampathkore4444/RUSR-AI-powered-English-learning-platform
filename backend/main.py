"""
FastAPI application entry point.

Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.database import engine
from common.exceptions import AppError, app_error_handler
from common.middleware import RequestTimingMiddleware
from routes import articles, vocabulary, words, review, auth, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hooks."""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    yield
    await engine.dispose()
    print("👋 Shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware ────────────────────────────────────────────

app.add_middleware(RequestTimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ───────────────────────────────────

app.add_exception_handler(AppError, app_error_handler)

# ── Routers ──────────────────────────────────────────────

app.include_router(auth.router, prefix=settings.API_PREFIX)
app.include_router(articles.router, prefix=settings.API_PREFIX)
app.include_router(vocabulary.router, prefix=settings.API_PREFIX)
app.include_router(words.router, prefix=settings.API_PREFIX)
app.include_router(review.router, prefix=settings.API_PREFIX)
app.include_router(users.router, prefix=settings.API_PREFIX)


# ── Health check ─────────────────────────────────────────

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}
