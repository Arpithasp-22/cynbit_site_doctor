"""Candidate-facing explanation.

Default is a deterministic template, so the prototype works offline with no API key.
If ANTHROPIC_API_KEY is set, the same structured facts are handed to an LLM that is only
allowed to rephrase them (no new skills, courses or numbers). Any failure falls back to
the template, so the UI never breaks because of the LLM.
"""
from __future__ import annotations

import json
import os

from .matcher import RoleMatch
from .pathway import LearningPath

DEFAULT_MODEL = "claude-sonnet-5-5"  # override with CLAUDE_MODEL

SYSTEM_PROMPT = (
    "You are a career coach inside a learning platform. You receive a JSON object of facts "
    "about a candidate's fit for a role. Write a short, encouraging explanation (max 120 words) "
    "in plain English. Use ONLY the facts provided: do not invent skills, courses, hours, "
    "or percentages. Mention matched strengths, the most important gaps, and the first course "
    "to take. Do not guarantee job outcomes."
)


def facts(match: RoleMatch, path: LearningPath) -> dict:
    return {
        "role": match.role.title,
        "fit_percent": round(match.score * 100),
        "matched_required_skills": sorted(match.matched_required),
        "missing_required_skills": sorted(match.missing_required, key=lambda s: -match.missing_required[s]),
        "learning_path": [
            {"course": st.course.title, "closes": st.closes, "hours": st.course.hours}
            for st in path.steps
        ],
        "total_hours": path.total_hours,
        "skills_not_covered_by_any_course": path.uncovered,
    }


def template_explanation(match: RoleMatch, path: LearningPath) -> str:
    f = facts(match, path)
    parts = [f"Your fit score for {f['role']} is {f['fit_percent']}%."]
    if f["matched_required_skills"]:
        parts.append("Strengths already on your resume: " + ", ".join(f["matched_required_skills"]) + ".")
    if f["missing_required_skills"]:
        parts.append("Core skills still missing: " + ", ".join(f["missing_required_skills"]) + ".")
    else:
        parts.append("You cover every core skill for this role.")
    if path.steps:
        first = path.steps[0]
        parts.append(
            f"Suggested first step: {first.course.title} ({first.course.hours}h), which closes "
            + ", ".join(first.closes) + f". The full path is about {path.total_hours} hours."
        )
    if path.uncovered:
        parts.append("No catalogue course yet covers: " + ", ".join(path.uncovered) + ".")
    return " ".join(parts)


def llm_explanation(match: RoleMatch, path: LearningPath) -> str | None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL),
            max_tokens=300,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": json.dumps(facts(match, path))}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip() or None
    except Exception:
        return None


def explain(match: RoleMatch, path: LearningPath, use_llm: bool = True) -> tuple[str, str]:
    """Return (text, source) where source is 'llm' or 'template'."""
    if use_llm:
        text = llm_explanation(match, path)
        if text:
            return text, "llm"
    return template_explanation(match, path), "template"
