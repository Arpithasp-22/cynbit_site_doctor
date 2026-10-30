"""Tiny ablation on the synthetic resumes: text-only vs skills-only vs hybrid.

IMPORTANT: 14 hand-written resumes written by the same author as the taxonomy. This is a
smoke test and a sanity check on the ranking logic, NOT evidence of real-world accuracy.
Run: python -m skillbridge.evaluate
"""
from __future__ import annotations

from .data import load_sample_resumes
from .matcher import RoleMatcher


def evaluate(modes=("text", "skills", "hybrid")) -> dict[str, dict[str, float]]:
    matcher = RoleMatcher()
    resumes = load_sample_resumes()
    results: dict[str, dict[str, float]] = {}
    for mode in modes:
        top1 = top3 = 0
        for r in resumes:
            ranked = [m.role.id for m in matcher.rank(r["text"], mode=mode)]
            top1 += ranked[0] == r["expected_role"]
            top3 += r["expected_role"] in ranked[:3]
        n = len(resumes)
        results[mode] = {"top1": top1 / n, "top3": top3 / n, "n": n}
    return results


def main() -> None:
    res = evaluate()
    print(f"{'mode':<8} {'top-1':>6} {'top-3':>6}   (n={next(iter(res.values()))['n']})")
    for mode, r in res.items():
        print(f"{mode:<8} {r['top1']:>6.0%} {r['top3']:>6.0%}")


if __name__ == "__main__":
    main()
