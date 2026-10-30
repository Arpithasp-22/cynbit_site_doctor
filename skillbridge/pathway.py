"""Learning-path generation: greedy weighted set cover over missing skills."""
from __future__ import annotations

from dataclasses import dataclass

from .data import Course, load_courses
from .matcher import RoleMatch


@dataclass
class PathStep:
    course: Course
    closes: list[str]  # missing skills this step closes
    value: int  # total role weight of those skills


@dataclass
class LearningPath:
    steps: list[PathStep]
    uncovered: list[str]  # missing skills no course teaches
    total_hours: int


def build_path(match: RoleMatch, courses: tuple[Course, ...] | None = None,
               include_nice_to_have: bool = False, max_steps: int = 6) -> LearningPath:
    courses = courses if courses is not None else load_courses()
    # Required gaps carry their role weight; nice-to-have gaps weigh 0.5 (kept as ints x2).
    remaining = {s: 2 * w for s, w in match.missing_required.items()}
    if include_nice_to_have:
        remaining.update({s: 1 for s in match.missing_nice})

    steps: list[PathStep] = []
    while remaining and len(steps) < max_steps:
        best, best_gain = None, 0.0
        for c in courses:
            if any(s.course.id == c.id for s in steps):
                continue
            closed = [s for s in c.skills if s in remaining]
            if not closed:
                continue
            value = sum(remaining[s] for s in closed)
            gain = value / c.hours  # value per hour of effort
            if gain > best_gain:
                best, best_gain = (c, closed, value), gain
        if best is None:
            break
        course, closed, value = best
        steps.append(PathStep(course, closed, value))
        for s in closed:
            remaining.pop(s)

    # Present in a sensible learning order: foundations before advanced modules.
    steps.sort(key=lambda st: (st.course.level, -st.value))
    return LearningPath(
        steps=steps,
        uncovered=sorted(remaining),
        total_hours=sum(st.course.hours for st in steps),
    )
