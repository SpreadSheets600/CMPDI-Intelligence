"""Keyword extraction with a dual-layer strategy: an Ollama prompt when a
generative backend is available, and a deterministic term-frequency fallback
with stopword filtering otherwise. Keywords double as document tags for
filtering and as a lexical search layer."""

import re
from collections import Counter

from backend.core.llm import get_backend

STOPWORDS = set("""the a an and or of to in for on with by from at as is are was were be been it its
this that these those their his her our your not no than then thus so such which who whom whose what
when where how all any both each few more most other some only own same too very can will just should
now also may might must shall would could during before after above below between under over again
further once here there why per annum year years total including respectively lakh crore report
page annex statement limited company ltd under against within without three two one four five during
being having said says under section sub part shall made make made may mr mrs""".split())

_WORD = re.compile(r"[A-Za-z][A-Za-z\-']+")


def _tf_keywords(text: str, k: int) -> list[str]:
    words = [w.lower() for w in _WORD.findall(text)]
    words = [w for w in words if w not in STOPWORDS and len(w) > 3]
    counts = Counter(words)
    # single words first, then frequent bigrams for domain terms like "coal seam"
    bigrams = Counter(zip(words, words[1:]))
    results = [w for w, _ in counts.most_common(k)]
    for (a, b), c in bigrams.most_common(k):
        if c >= 3 and len(results) < k and a not in results and b not in results:
            results.append(f"{a} {b}")
    return results[:k]


def extract_keywords(text: str, k: int = 6) -> tuple[list[str], str]:
    """Returns (keywords, source) where source is 'llm' or 'tf'."""
    if not text.strip():
        return [], "tf"
    backend = get_backend()
    prompt = (
        "Extract the most representative topics from this mining/geological "
        "document excerpt. Reply with exactly "
        f"{k} keywords as a comma-separated list. Use lowercase single words or "
        "two-word terms. No numbering, no explanations.\n\n"
        f"Text:\n{text[:4000]}"
    )
    raw = backend.generate(
        "You extract keywords. Reply with the comma-separated list only.",
        prompt,
    )
    if raw:
        words = [w.strip().lower() for w in re.split(r"[,\n]", raw)]
        words = [w for w in words if 2 < len(w) < 40 and not w.startswith("-")][:k]
        if words:
            return words, "llm"
    return _tf_keywords(text, k), "tf"
