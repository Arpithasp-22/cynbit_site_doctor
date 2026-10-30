"""Command-line entry point: python -m skillbridge.cli resume.txt [--top 3]"""
from __future__ import annotations

import argparse
import sys

from .explain import explain
from .matcher import RoleMatcher
from .pathway import build_path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Match a resume to roles and build a learning path.")
    p.add_argument("resume", help="Path to a .txt resume, or '-' for stdin")
    p.add_argument("--top", type=int, default=3)
    p.add_argument("--no-llm", action="store_true", help="Skip the optional LLM explanation")
    args = p.parse_args(argv)

    text = sys.stdin.read() if args.resume == "-" else open(args.resume, encoding="utf-8").read()
    matches = RoleMatcher().rank(text)[: args.top]
    for i, m in enumerate(matches, 1):
        path = build_path(m)
        msg, src = explain(m, path, use_llm=not args.no_llm)
        print(f"\n#{i} {m.role.title}  fit={m.score:.0%}  (skills {m.skill_score:.0%}, text {m.text_score:.0%})")
        print(f"   matched: {', '.join(sorted(m.matched_required)) or '-'}")
        print(f"   missing: {', '.join(m.missing_required) or '-'}")
        for st in path.steps:
            print(f"   -> {st.course.title} [{st.course.hours}h] closes {', '.join(st.closes)}")
        print(f"   [{src}] {msg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
