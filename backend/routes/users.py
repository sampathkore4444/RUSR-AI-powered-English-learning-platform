"""
User routes — profile and GDPR deletion.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import get_db_session
from core.auth import get_current_user
from models.user import User
from models.article import Article, ArticleParagraph, ArticleSentence
from models.token import SentenceToken
from models.vocabulary import UserVocabulary
from models.learning_event import LearningEvent
from models.embedding import SentenceEmbedding
from schemas.user import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(user: User = Depends(get_current_user)):
    """Get the current user's profile."""
    return user


@router.delete("/me", status_code=204)
async def delete_my_account(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    GDPR-compliant account deletion.

    Deletes all user data: articles, vocabulary, learning events, embeddings, and the user.
    """
    user_id = user.id

    # Delete in dependency order (foreign keys)
    # 1. Sentence embeddings (depends on sentences)
    await db.execute(
        delete(SentenceEmbedding).where(
            SentenceEmbedding.sentence_id.in_(
                select(SentenceToken.sentence_id).where(
                    SentenceToken.sentence_id.in_(
                        select(ArticleSentence.id).where(
                            ArticleSentence.paragraph_id.in_(
                                select(ArticleParagraph.id).where(
                                    ArticleParagraph.article_id.in_(
                                        select(Article.id).where(Article.user_id == user_id)
                                    )
                                )
                            )
                        )
                    )
                )
            )
        )
    )

    # 2. Tokens (depends on sentences)
    await db.execute(
        delete(SentenceToken).where(
            SentenceToken.sentence_id.in_(
                select(ArticleSentence.id).where(
                    ArticleSentence.paragraph_id.in_(
                        select(ArticleParagraph.id).where(
                            ArticleParagraph.article_id.in_(
                                select(Article.id).where(Article.user_id == user_id)
                            )
                        )
                    )
                )
            )
        )
    )

    # 3. Sentences
    await db.execute(
        delete(ArticleSentence).where(
            ArticleSentence.paragraph_id.in_(
                select(ArticleParagraph.id).where(
                    ArticleParagraph.article_id.in_(
                        select(Article.id).where(Article.user_id == user_id)
                    )
                )
            )
        )
    )

    # 4. Paragraphs
    await db.execute(
        delete(ArticleParagraph).where(
            ArticleParagraph.article_id.in_(
                select(Article.id).where(Article.user_id == user_id)
            )
        )
    )

    # 5. Articles
    await db.execute(delete(Article).where(Article.user_id == user_id))

    # 6. Learning events
    await db.execute(delete(LearningEvent).where(LearningEvent.user_id == user_id))

    # 7. Vocabulary
    await db.execute(delete(UserVocabulary).where(UserVocabulary.user_id == user_id))

    # 8. User
    await db.delete(user)
    await db.flush()


# Need select for subqueries
from sqlalchemy import select
