"""
Word Intelligence service — the "tap a word" pipeline.

Orchestrates:
  1. Dictionary lookup (deterministic) — definition, POS, synonyms, pronunciation
  2. NLP processing (deterministic) — lemma, POS tagging
  3. AI context explanation (LLM) — meaning in context, example sentence

This is the core differentiator of the app.
"""

from schemas.word import (
    WordInspectRequest,
    WordInspectResponse,
    DictionaryInfo,
    ExplainRequest,
    ExplainResponse,
)
from services.nlp_service import get_lemma, get_pos
from services.dictionary_service import lookup_word
from services.ai_service import generate_context_meaning, generate_example, generate_explanation


async def inspect_word(payload: WordInspectRequest) -> WordInspectResponse:
    """
    Full word intelligence pipeline.

    Steps:
      1. Lemmatize the tapped word
      2. Look up dictionary data (definition, POS, synonyms, pronunciation)
      3. Get AI-powered meaning in context
      4. Generate an example sentence
    """
    # Step 1: NLP — get lemma and POS
    lemma = await get_lemma(payload.word)
    pos = await get_pos(payload.word)

    # Step 2: Dictionary lookup (includes pronunciation)
    dict_data = await lookup_word(lemma)

    # Pick the best matching definition for this POS
    definition = _pick_definition(dict_data["definitions"], pos)

    # Step 3: AI — meaning in this specific context
    context_meaning = await generate_context_meaning(payload.word, payload.sentence)

    # Step 4: AI — example sentence
    example = await generate_example(lemma, definition)

    return WordInspectResponse(
        word=payload.word,
        lemma=lemma,
        dictionary=DictionaryInfo(
            definition=definition,
            pos=pos,
            pronunciation=dict_data.get("pronunciation"),  # ← wired through
            synonyms=dict_data["synonyms"][:5],
        ),
        context_meaning=context_meaning,
        example=example,
    )


async def explain_sentence(payload: ExplainRequest) -> ExplainResponse:
    """
    AI explanation of a selected sentence.

    Supports multiple explanation styles via the `action` parameter.
    """
    explanation = await generate_explanation(payload.sentence, payload.action)

    return ExplainResponse(
        original=payload.sentence,
        explanation=explanation,
        action=payload.action,
    )


# ── Private helpers ──────────────────────────────────────


def _pick_definition(definitions: list[dict], target_pos: str) -> str:
    """Pick the definition that best matches the detected POS."""
    if not definitions:
        return "No definition found"

    target_pos_lower = target_pos.lower()

    # Try to find a matching POS
    for defn in definitions:
        if defn["pos"] == target_pos_lower:
            return defn["definition"]

    # Fallback: return the first definition
    return definitions[0]["definition"]
