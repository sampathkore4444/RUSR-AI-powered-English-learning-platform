"""
NLP service — spaCy-based tokenization, POS tagging, lemmatization, and sentence splitting.

This is a deterministic layer: no LLM calls, pure linguistic processing.
"""

import spacy

# Load spaCy model once at module level
try:
    _nlp = spacy.load("en_core_web_sm")
except OSError:
    _nlp = None


def _get_nlp():
    if _nlp is None:
        raise RuntimeError(
            "spaCy model 'en_core_web_sm' not found. "
            "Run: python -m spacy download en_core_web_sm"
        )
    return _nlp


async def process_sentence(sentence: str) -> list[dict]:
    """
    Process a sentence and return annotated tokens.

    Returns:
        [
            {"text": "The", "lemma": "the", "pos": "DET"},
            {"text": "curb", "lemma": "curb", "pos": "NOUN"},
            ...
        ]
    """
    nlp = _get_nlp()
    doc = nlp(sentence)

    tokens = []
    for token in doc:
        if token.is_space:
            continue
        tokens.append({
            "text": token.text,
            "lemma": token.lemma_.lower(),
            "pos": token.pos_,
        })
    return tokens


async def split_sentences(text: str) -> list[str]:
    """
    Split text into sentences using spaCy's sentencizer.

    More accurate than regex — handles abbreviations, numbers, etc.
    """
    nlp = _get_nlp()
    doc = nlp(text)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
    return sentences


async def get_lemma(word: str) -> str:
    """Return the base form (lemma) of a word."""
    nlp = _get_nlp()
    doc = nlp(word)
    if doc:
        return doc[0].lemma_.lower()
    return word.lower()


async def get_pos(word: str) -> str:
    """Return the part-of-speech tag for a word."""
    nlp = _get_nlp()
    doc = nlp(word)
    if doc:
        return doc[0].pos_
    return "UNKNOWN"
