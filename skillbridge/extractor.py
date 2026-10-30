"""Rule-based skill extraction against the taxonomy.

Why rules and not an LLM here: the taxonomy is closed and small, matching has to be
deterministic and auditable (a candidate can ask "why was this skill detected?"),
and it costs nothing per resume. An LLM/embedding fallback for unseen skills is
described in docs/technical_approach.md as the next iteration.
"""
from __future__ import annotations

import re
from functools import lru_cache

from .data import load_taxonomy

# A skill token must not be glued to other word characters. '+', '#' and '.' are
# treated as part of tokens so "c++" and "node.js" work, and "sql" does not match
# inside "mysql" (that is covered by an explicit alias instead).
_LEFT = r"(?<![a-z0-9+#.])"
_RIGHT = r"(?![a-z0-9+#])"


@lru_cache(maxsize=1)
def _patterns() -> dict[str, re.Pattern]:
    patterns = {}
    for skill, meta in load_taxonomy().items():
        names = [skill, *meta.get("aliases", [])]
        # Longest first so "retrieval augmented generation" wins over shorter forms.
        names.sort(key=len, reverse=True)
        alternation = "|".join(re.escape(n) for n in names)
        patterns[skill] = re.compile(f"{_LEFT}(?:{alternation}){_RIGHT}")
    return patterns


def normalise(text: str) -> str:
    text = text.lower()
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text)


def extract_skills(text: str) -> set[str]:
    """Return the set of canonical skills mentioned in `text`."""
    clean = normalise(text)
    return {skill for skill, pat in _patterns().items() if pat.search(clean)}


def extract_with_evidence(text: str, window: int = 30) -> dict[str, str]:
    """Return {skill: snippet} so every detected skill can be justified to the user."""
    clean = normalise(text)
    out: dict[str, str] = {}
    for skill, pat in _patterns().items():
        m = pat.search(clean)
        if m:
            start, end = max(0, m.start() - window), min(len(clean), m.end() + window)
            out[skill] = clean[start:end].strip()
    return out
