"""
Word intelligence schemas (tap-to-lookup, AI explain).
"""

from pydantic import BaseModel


class WordInspectRequest(BaseModel):
    """Request body: user taps a word in an article."""
    word: str
    sentence: str
    sentence_id: str | None = None


class DictionaryInfo(BaseModel):
    definition: str
    pos: str
    pronunciation: str | None = None
    synonyms: list[str] = []


class WordInspectResponse(BaseModel):
    """Response: full word intelligence card."""
    word: str
    lemma: str
    dictionary: DictionaryInfo
    context_meaning: str | None = None
    example: str | None = None


class ExplainRequest(BaseModel):
    """Request body: AI explanation of a selected sentence."""
    sentence: str
    action: str = "simple"  # simple | grammar | vocabulary | examples | translate


class ExplainResponse(BaseModel):
    """Response: AI-generated explanation."""
    original: str
    explanation: str
    action: str
