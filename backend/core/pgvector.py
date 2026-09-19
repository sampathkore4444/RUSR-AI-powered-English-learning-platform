"""
pgvector integration for semantic search.

Provides:
  - Vector column type for SQLAlchemy
  - Embedding generation via sentence-transformers
  - Similarity search helpers
"""

from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings

settings = get_settings()

# ── Embedding generation ─────────────────────────────────

_embedding_model = None


def _get_embedding_model():
    """Lazy-load the sentence-transformers model."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


async def generate_embedding(text_content: str) -> list[float]:
    """Generate a 384-dim embedding vector for a piece of text."""
    model = _get_embedding_model()
    embedding = model.encode(text_content, normalize_embeddings=True)
    return embedding.tolist()


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts at once (more efficient)."""
    model = _get_embedding_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return [e.tolist() for e in embeddings]


# ── Similarity search ────────────────────────────────────


async def find_similar_sentences(
    db: AsyncSession,
    query_embedding: list[float],
    user_id: str,
    limit: int = 5,
    similarity_threshold: float = 0.3,
) -> list[dict]:
    """
    Find sentences similar to the query embedding using cosine distance.

    Returns list of {sentence_id, text, similarity_score}.
    """
    sql = text("""
        SELECT
            s.id as sentence_id,
            s.text,
            1 - (e.embedding <=> :query_vec) as similarity
        FROM sentence_embeddings e
        JOIN article_sentences s ON s.id = e.sentence_id
        JOIN article_paragraphs p ON p.id = s.paragraph_id
        JOIN articles a ON a.id = p.article_id
        WHERE a.user_id = :user_id
          AND 1 - (e.embedding <=> :query_vec) > :threshold
        ORDER BY e.embedding <=> :query_vec
        LIMIT :limit
    """)

    result = await db.execute(
        sql,
        {
            "query_vec": str(query_embedding),
            "user_id": user_id,
            "threshold": similarity_threshold,
            "limit": limit,
        },
    )

    return [
        {"sentence_id": row[0], "text": row[1], "similarity": row[2]}
        for row in result.fetchall()
    ]


# ── pgvector extension setup ─────────────────────────────


async def ensure_pgvector_extension(db: AsyncSession) -> None:
    """Create the pgvector extension if it doesn't exist."""
    await db.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    await db.flush()
