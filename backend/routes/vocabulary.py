"""
Vocabulary routes — personal word store CRUD, word of the day, and export (protected).
"""

import csv
import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db_session
from core.auth import get_current_user
from models.user import User
from schemas.vocabulary import (
    VocabularySave,
    VocabularyUpdate,
    VocabularyResponse,
    VocabularyListResponse,
    WordOfDayResponse,
)
from services import vocabulary_service

router = APIRouter(prefix="/vocabulary", tags=["Vocabulary"])


@router.post("", response_model=VocabularyResponse, status_code=201)
async def save_word(
    payload: VocabularySave,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Save a word to personal vocabulary."""
    vocab = await vocabulary_service.save_word(db, user.id, payload)
    return vocab


@router.get("", response_model=VocabularyListResponse)
async def list_vocabulary(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List saved vocabulary words."""
    words, total = await vocabulary_service.get_vocabulary(db, user.id, offset, limit)
    return VocabularyListResponse(vocabulary=words, total=total)


@router.get("/word-of-the-day", response_model=WordOfDayResponse | None)
async def get_word_of_the_day(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get the word of the day — selected from the user's vocabulary
    based on spaced repetition priority.
    """
    result = await vocabulary_service.get_word_of_day(db, user.id)
    return result


@router.get("/export/csv")
async def export_vocabulary_csv(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Export all vocabulary as a CSV file.
    Columns: word, lemma, meaning, difficulty, mastery_level, times_reviewed, next_review_date
    """
    words, _ = await vocabulary_service.get_vocabulary(db, user.id, offset=0, limit=10000)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["word", "lemma", "meaning", "difficulty", "mastery_level", "times_reviewed", "next_review_date"])

    for w in words:
        writer.writerow([
            w.word,
            w.lemma,
            w.meaning or "",
            w.difficulty,
            round(w.mastery_level, 2),
            w.times_reviewed,
            w.next_review_date.isoformat() if w.next_review_date else "",
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=vocabulary_{user.id[:8]}.csv"},
    )


@router.get("/export/anki")
async def export_vocabulary_anki(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Export vocabulary as Anki-compatible tab-separated file.
    Format: front<tab>back<tab>tags
    Front: word
    Back: meaning | difficulty | mastery
    Tags: RUSR Easy/Medium/Hard
    """
    words, _ = await vocabulary_service.get_vocabulary(db, user.id, offset=0, limit=10000)

    output = io.StringIO()
    for w in words:
        # Anki format: front \t back \t tags
        front = w.word
        back_parts = [w.meaning or "No meaning"]
        if w.difficulty:
            back_parts.append(f"Difficulty: {w.difficulty}")
        back_parts.append(f"Mastery: {round(w.mastery_level * 100)}%")
        back = " | ".join(back_parts)

        tags = f"RUSR {w.difficulty}"

        output.write(f"{front}\t{back}\t{tags}\n")

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=vocabulary_anki_{user.id[:8]}.txt"},
    )


@router.get("/{vocab_id}", response_model=VocabularyResponse)
async def get_vocabulary_word(
    vocab_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Get details of a saved word."""
    vocab = await vocabulary_service.get_vocabulary_word(db, vocab_id)
    return vocab


@router.put("/{vocab_id}", response_model=VocabularyResponse)
async def update_vocabulary_word(
    vocab_id: str,
    payload: VocabularyUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Update personal note, meaning, or difficulty."""
    vocab = await vocabulary_service.update_vocabulary(db, vocab_id, payload)
    return vocab


@router.delete("/{vocab_id}", status_code=204)
async def delete_vocabulary_word(
    vocab_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Remove a word from personal vocabulary."""
    await vocabulary_service.delete_vocabulary(db, vocab_id)
