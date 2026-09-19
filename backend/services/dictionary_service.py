"""
Dictionary service — WordNet definitions, synonyms, and pronunciation.

Uses:
  - NLTK WordNet for definitions and synonyms
  - eng-to-ipa for IPA pronunciation (no network needed)
  - Redis cache for fast repeated lookups
"""

from nltk.corpus import wordnet as wn
from core.cache import (
    cache_dictionary, get_cached_dictionary,
    cache_pronunciation, get_cached_pronunciation,
)

# Try to import pronunciation library
try:
    from eng_to_ipa import convert as ipa_convert
    _HAS_PRONUNCIATION = True
except ImportError:
    _HAS_PRONUNCIATION = False


async def lookup_word(word: str) -> dict:
    """
    Look up a word and return structured data.
    Results are cached in Redis for 7 days.
    """
    # Check cache first
    cached = await get_cached_dictionary(word)
    if cached is not None:
        return cached

    # Cache miss — do the actual lookup
    synsets = wn.synsets(word)

    if not synsets:
        pron = await get_pronunciation(word)
        result = {
            "definitions": [],
            "synonyms": [],
            "pos_tags": [],
            "pronunciation": pron,
        }
        await cache_dictionary(word, result)
        return result

    definitions = []
    all_synonyms = set()
    pos_tags = set()

    for synset in synsets[:5]:
        pos = synset.pos()
        pos_label = _pos_map(pos)
        pos_tags.add(pos_label)

        definitions.append({
            "pos": pos_label,
            "definition": synset.definition(),
        })

        for lemma in synset.lemmas():
            name = lemma.name().replace("_", " ")
            if name.lower() != word.lower():
                all_synonyms.add(name)

    pron = await get_pronunciation(word)

    result = {
        "definitions": definitions,
        "synonyms": sorted(all_synonyms)[:10],
        "pos_tags": sorted(pos_tags),
        "pronunciation": pron,
    }

    await cache_dictionary(word, result)
    return result


async def get_pronunciation(word: str) -> str | None:
    """
    Get IPA pronunciation for a word.
    Cached in Redis for 30 days.
    """
    # Check cache
    cached = await get_cached_pronunciation(word)
    if cached is not None:
        return cached

    if not _HAS_PRONUNCIATION:
        return None

    try:
        ipa = ipa_convert(word)
        if ipa and ipa != word and "*" not in ipa:
            result = f"/{ipa}/"
            await cache_pronunciation(word, result)
            return result
        await cache_pronunciation(word, None)
        return None
    except Exception:
        return None


def _pos_map(wn_pos: str) -> str:
    """Map WordNet POS codes to human-readable labels."""
    mapping = {
        "n": "noun",
        "v": "verb",
        "a": "adjective",
        "s": "adjective",
        "r": "adverb",
    }
    return mapping.get(wn_pos, "unknown")
