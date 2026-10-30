"""Hybrid role matcher: weighted skill coverage + TF-IDF text similarity."""
from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .data import Role, load_roles
from .extractor import extract_skills

SKILL_WEIGHT = 0.7
TEXT_WEIGHT = 0.3
NICE_TO_HAVE_FACTOR = 0.5  # a nice-to-have skill counts half of a weight-1 required skill


@dataclass
class RoleMatch:
    role: Role
    score: float
    skill_score: float
    text_score: float
    matched_required: dict[str, int] = field(default_factory=dict)
    missing_required: dict[str, int] = field(default_factory=dict)
    matched_nice: list[str] = field(default_factory=list)
    missing_nice: list[str] = field(default_factory=list)


def skill_coverage(role: Role, skills: set[str]) -> tuple[float, dict, dict, list, list]:
    matched = {s: w for s, w in role.required.items() if s in skills}
    missing = {s: w for s, w in role.required.items() if s not in skills}
    nice_hit = [s for s in role.nice_to_have if s in skills]
    nice_miss = [s for s in role.nice_to_have if s not in skills]

    num = sum(matched.values()) + NICE_TO_HAVE_FACTOR * len(nice_hit)
    den = sum(role.required.values()) + NICE_TO_HAVE_FACTOR * len(role.nice_to_have)
    return (num / den if den else 0.0), matched, missing, nice_hit, nice_miss


class RoleMatcher:
    def __init__(self, roles: tuple[Role, ...] | None = None):
        self.roles = tuple(roles) if roles is not None else load_roles()
        self._vec = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        self._role_matrix = self._vec.fit_transform([r.text() for r in self.roles])

    def _text_scores(self, resume_text: str) -> list[float]:
        sims = cosine_similarity(self._vec.transform([resume_text]), self._role_matrix)[0]
        top = sims.max()
        # Normalise to the best role so the text signal is comparable across resumes.
        return [float(s / top) if top > 0 else 0.0 for s in sims]

    def rank(self, resume_text: str, mode: str = "hybrid") -> list[RoleMatch]:
        """Rank roles. mode: 'hybrid' (default), 'skills' or 'text' (used for ablations)."""
        skills = extract_skills(resume_text)
        text_scores = self._text_scores(resume_text)
        results = []
        for role, t_score in zip(self.roles, text_scores):
            s_score, matched, missing, nice_hit, nice_miss = skill_coverage(role, skills)
            if mode == "skills":
                score = s_score
            elif mode == "text":
                score = t_score
            else:
                score = SKILL_WEIGHT * s_score + TEXT_WEIGHT * t_score
            results.append(
                RoleMatch(role, score, s_score, t_score, matched, missing, nice_hit, nice_miss)
            )
        results.sort(key=lambda m: m.score, reverse=True)
        return results
