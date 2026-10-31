"""Turn issues into a scorecard, and compare two scans."""
from __future__ import annotations

from dataclasses import dataclass

from .checks import CATEGORIES, SEV_WEIGHT, Issue, Result

PENALTY_SCALE = 2.0  # heuristic: one high issue on every page costs about 20 points in its category


@dataclass
class Scorecard:
    overall: int | None
    by_category: dict[str, int | None]  # None = not checked in this scan
    counts: dict[str, int]
    quick_wins: list[Issue]


def issue_penalty(issue: Issue, total_pages: int) -> float:
    share = min(1.0, len(issue.pages) / max(1, total_pages))
    return SEV_WEIGHT[issue.severity] * (0.5 + 0.5 * share)


def score(result: Result, total_pages: int) -> Scorecard:
    by_cat: dict[str, int | None] = {}
    for cat in CATEGORIES:
        if cat not in result.checked:
            by_cat[cat] = None
            continue
        penalty = sum(issue_penalty(i, total_pages) for i in result.issues if i.category == cat)
        by_cat[cat] = max(0, round(100 - PENALTY_SCALE * penalty))
    scored = [v for v in by_cat.values() if v is not None]
    counts = {s: sum(1 for i in result.issues if i.severity == s) for s in ("high", "medium", "low")}
    counts["total"] = len(result.issues)
    return Scorecard(
        overall=round(sum(scored) / len(scored)) if scored else None,
        by_category=by_cat, counts=counts,
        quick_wins=[i for i in result.issues if i.quick_win],
    )


def compare(before: list[Issue], after: list[Issue]) -> dict[str, list[str]]:
    """What changed between two scans (matched on issue id)."""
    b, a = {i.id: i for i in before}, {i.id: i for i in after}
    return {
        "resolved": sorted(b[k].title for k in b.keys() - a.keys()),
        "new": sorted(a[k].title for k in a.keys() - b.keys()),
        "remaining": sorted(a[k].title for k in a.keys() & b.keys()),
    }
