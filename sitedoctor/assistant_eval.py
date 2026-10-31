"""Evaluate and tune the assistant's answer/decline decision.

Items alternate between a tuning half (even index) and a test half (odd index). Thresholds are chosen on
the tuning half only and reported on the test half. With about 34 items the numbers are indicative, not
precise, and the questions were written by the author from the same snapshot (optimistic).
Run: python -m sitedoctor.assistant_eval
"""
from __future__ import annotations

import itertools
import json
from urllib.parse import urlparse

from .assistant import SiteAssistant
from .crawler import DATA_DIR, load_snapshot


def load_items() -> list[dict]:
    return json.loads((DATA_DIR / "assistant_eval.json").read_text(encoding="utf-8"))["items"]


def evaluate(assistant: SiteAssistant, items: list[dict], score_t: float, cov_t: float) -> dict:
    ans_ok = ans_total = dec_ok = dec_total = 0
    retrieval_hit = 0
    for it in items:
        top = assistant.retrieve(it["q"])
        score = top[0][1]
        cov = assistant.coverage(it["q"], top)
        answered = score >= score_t and cov >= cov_t
        if it["answerable"]:
            ans_total += 1
            path_ok = urlparse(top[0][0].url).path.rstrip("/") or "/"
            kw = it["keyword"].lower()
            in_top = any(kw in c.text.lower() for c, _ in top)
            retrieval_hit += (path_ok in it["paths"]) and in_top
            ans_ok += answered and (path_ok in it["paths"]) and in_top
        else:
            dec_total += 1
            dec_ok += not answered
    return {
        "answerable_correct": ans_ok / ans_total if ans_total else 0.0,
        "retrieval_hit_at1": retrieval_hit / ans_total if ans_total else 0.0,
        "unanswerable_declined": dec_ok / dec_total if dec_total else 0.0,
        "n_answerable": ans_total, "n_unanswerable": dec_total,
    }


def balanced(m: dict) -> float:
    return 0.5 * (m["answerable_correct"] + m["unanswerable_declined"])


def tune(assistant: SiteAssistant, items: list[dict]):
    dev = items[0::2]
    grid = list(itertools.product([0.0, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15, 0.20], [0.0, 0.4, 0.5, 0.6, 0.7, 0.8]))
    best = max(grid, key=lambda g: (balanced(evaluate(assistant, dev, *g)), g[0] + g[1]))
    return best


def main() -> None:
    assistant = SiteAssistant(load_snapshot())
    items = load_items()
    test = items[1::2]
    print("Baseline A: always answer            ", {k: round(v, 2) for k, v in evaluate(assistant, test, 0.0, 0.0).items()})
    print("Baseline B: score threshold only 0.10", {k: round(v, 2) for k, v in evaluate(assistant, test, 0.10, 0.0).items()})
    best = tune(assistant, items)
    print(f"Tuned on even items -> score>={best[0]}, coverage>={best[1]}")
    print("Test half (odd items)               ", {k: round(v, 2) for k, v in evaluate(assistant, test, *best).items()})
    print("All items at tuned thresholds       ", {k: round(v, 2) for k, v in evaluate(assistant, items, *best).items()})
    print("\nSweep on all items (score, coverage -> answerable correct / unanswerable declined)")
    for s, c in [(0.0, 0.0), (0.06, 0.0), (0.10, 0.0), (0.0, 0.6), (0.06, 0.6), (0.10, 0.6), (0.10, 0.8)]:
        m = evaluate(assistant, items, s, c)
        print(f"  {s:.2f}, {c:.1f} -> {m['answerable_correct']:.0%} / {m['unanswerable_declined']:.0%}")


if __name__ == "__main__":
    main()
