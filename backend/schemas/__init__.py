"""
Pydantic schemas for request validation and response serialisation.
"""

from schemas.article import (
    ArticleCreate,
    ArticleCreateFromURL,
    ArticleResponse,
    ArticleListResponse,
    ParagraphResponse,
    SentenceResponse,
)
from schemas.vocabulary import (
    VocabularySave,
    VocabularyUpdate,
    VocabularyResponse,
    VocabularyListResponse,
)
from schemas.word import (
    WordInspectRequest,
    WordInspectResponse,
    ExplainRequest,
    ExplainResponse,
)
from schemas.review import (
    ReviewDueResponse,
    ReviewAnswerRequest,
    ReviewAnswerResponse,
    ReviewStatsResponse,
)
from schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse

__all__ = [
    "ArticleCreate",
    "ArticleCreateFromURL",
    "ArticleResponse",
    "ArticleListResponse",
    "ParagraphResponse",
    "SentenceResponse",
    "VocabularySave",
    "VocabularyUpdate",
    "VocabularyResponse",
    "VocabularyListResponse",
    "WordInspectRequest",
    "WordInspectResponse",
    "ExplainRequest",
    "ExplainResponse",
    "ReviewDueResponse",
    "ReviewAnswerRequest",
    "ReviewAnswerResponse",
    "ReviewStatsResponse",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "TokenResponse",
]
