"""Loaders for the JSON data files in ./data."""
from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@dataclass(frozen=True)
class Role:
    id: str
    title: str
    description: str
    required: dict[str, int]
    nice_to_have: tuple[str, ...]

    def text(self) -> str:
        """Text used for the semantic (TF-IDF) side of the matcher."""
        skills = " ".join(list(self.required) + list(self.nice_to_have))
        return f"{self.title}. {self.description} {skills}"


@dataclass(frozen=True)
class Course:
    id: str
    title: str
    track: str
    level: int
    hours: int
    skills: tuple[str, ...]


def _read(name: str):
    with open(DATA_DIR / name, encoding="utf-8") as fh:
        return json.load(fh)


@lru_cache(maxsize=None)
def load_taxonomy() -> dict[str, dict]:
    return _read("skills.json")


@lru_cache(maxsize=None)
def load_roles() -> tuple[Role, ...]:
    return tuple(
        Role(
            id=r["id"],
            title=r["title"],
            description=r["description"],
            required=dict(r["required"]),
            nice_to_have=tuple(r.get("nice_to_have", [])),
        )
        for r in _read("roles.json")
    )


@lru_cache(maxsize=None)
def load_courses() -> tuple[Course, ...]:
    return tuple(
        Course(
            id=c["id"],
            title=c["title"],
            track=c["track"],
            level=c["level"],
            hours=c["hours"],
            skills=tuple(c["skills"]),
        )
        for c in _read("courses.json")["courses"]
    )


def load_sample_resumes() -> list[dict]:
    return _read("sample_resumes.json")["resumes"]


def validate() -> list[str]:
    """Return a list of data-consistency problems (empty list means OK)."""
    taxonomy = load_taxonomy()
    problems: list[str] = []
    for role in load_roles():
        for skill in list(role.required) + list(role.nice_to_have):
            if skill not in taxonomy:
                problems.append(f"role {role.id}: unknown skill '{skill}'")
    for course in load_courses():
        for skill in course.skills:
            if skill not in taxonomy:
                problems.append(f"course {course.id}: unknown skill '{skill}'")
    return problems
