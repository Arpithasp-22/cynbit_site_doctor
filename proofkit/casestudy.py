"""Evidence-gated case-study drafter.

Rule: a metric is only published if it has a baseline, a time period, a source and has been
verified. Everything else is held back and turned into a checklist of what to ask the client.
The optional LLM step may only improve wording: a guardrail rejects its output if any number
is added or removed.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_MODEL = "claude-sonnet-5-5"  # override with CLAUDE_MODEL

POLISH_PROMPT = (
    "You edit a draft client case study for a software company's website. Improve flow and tone "
    "only. Keep every number, name, unit, date and source EXACTLY as written. Do not add facts, "
    "claims, superlatives or numbers. Keep the markdown headings and the final draft notice."
)


@dataclass
class Metric:
    name: str
    value: float | str
    unit: str = ""
    baseline: float | str | None = None
    timeframe: str | None = None
    source: str | None = None
    verified: bool = False

    def missing(self) -> list[str]:
        gaps = []
        if self.baseline in (None, ""):
            gaps.append("baseline (the value before the work)")
        if not self.timeframe:
            gaps.append("time period")
        if not self.source:
            gaps.append("source (tool or report)")
        if not self.verified:
            gaps.append("client confirmation")
        return gaps

    def publishable(self) -> bool:
        return not self.missing()

    def change_pct(self) -> float | None:
        try:
            base, val = float(self.baseline), float(self.value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        return None if base == 0 else (val - base) / base * 100


@dataclass
class Evidence:
    client: str
    industry: str = ""
    problem: str = ""
    solution: str = ""
    services: list[str] = field(default_factory=list)
    quote: dict | None = None
    metrics: list[Metric] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "Evidence":
        return cls(
            client=d["client"], industry=d.get("industry", ""), problem=d.get("problem", ""),
            solution=d.get("solution", ""), services=list(d.get("services", [])),
            quote=d.get("quote"), metrics=[Metric(**m) for m in d.get("metrics", [])],
        )


@dataclass
class Draft:
    markdown: str
    published: list[Metric]
    held_back: list[tuple[Metric, list[str]]]


def load_sample_evidence() -> list[Evidence]:
    with open(DATA_DIR / "sample_evidence.json", encoding="utf-8") as fh:
        return [Evidence.from_dict(e) for e in json.load(fh)["evidence"]]


def _fmt(x: float | str) -> str:
    if isinstance(x, str):
        return x
    return f"{x:,.0f}" if float(x).is_integer() else f"{x:,.1f}"


def _result_line(m: Metric, tag: str = "") -> str:
    unit = f" {m.unit}" if m.unit else ""
    pct = m.change_pct()
    if m.baseline not in (None, "") and pct is not None:
        core = f"{_fmt(m.baseline)} to {_fmt(m.value)}{unit} ({pct:+.0f}%)"
    else:
        core = f"{_fmt(m.value)}{unit}"
    when = f", {m.timeframe}" if m.timeframe else ""
    src = f" Source: {m.source}." if m.source else ""
    return f"- **{m.name}:** {core}{when}.{src}{tag}"


def draft(ev: Evidence, include_unverified: bool = False) -> Draft:
    published = [m for m in ev.metrics if m.publishable()]
    held = [(m, m.missing()) for m in ev.metrics if not m.publishable()]

    lines = [f"# {ev.client}", ""]
    if ev.industry or ev.services:
        meta = " | ".join(x for x in (ev.industry, ", ".join(ev.services)) if x)
        lines += [f"*{meta}*", ""]
    if ev.problem:
        lines += ["## The challenge", ev.problem, ""]
    if ev.solution:
        lines += ["## What we did", ev.solution, ""]

    lines.append("## Results")
    if published or (include_unverified and held):
        lines += [_result_line(m) for m in published]
        if include_unverified:
            lines += [_result_line(m, " **[UNVERIFIED, do not publish]**") for m, _ in held]
    else:
        lines.append("No verified metrics yet. Add evidence before publishing.")
    lines.append("")

    q = ev.quote
    if q and q.get("consent") and q.get("text"):
        who = ", ".join(x for x in (q.get("person"), q.get("role")) if x)
        lines += ["## In the client's words", f"> {q['text']}", f"> {who}" if who else "", ""]

    lines.append("*DRAFT: requires client approval before publishing.*")
    return Draft("\n".join(lines), published, held)


def evidence_request(ev: Evidence) -> str:
    """A checklist the team can send to the client to fill the gaps."""
    d = draft(ev)
    items: list[str] = []
    for m, gaps in d.held_back:
        unit = "" if not m.unit else (m.unit if m.unit == "%" else f" {m.unit}")
        items.append(f"- **{m.name}** (currently {_fmt(m.value)}{unit}): please provide "
                     + "; ".join(gaps) + ".")
    if ev.quote and not ev.quote.get("consent"):
        items.append("- **Testimonial:** written permission to publish the quote with name and role.")
    if not ev.quote:
        items.append("- **Testimonial:** a short quote and permission to publish it.")
    if not items:
        return "Nothing missing. Send the draft for client approval."
    return f"Evidence needed for {ev.client}:\n" + "\n".join(items)


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", "") for n in _NUM.findall(text)}


def numbers_preserved(original: str, edited: str) -> bool:
    """Guardrail: the edited text must contain exactly the same set of numbers."""
    return numbers_in(original) == numbers_in(edited)


def polish(markdown: str) -> tuple[str, str]:
    """Optional LLM wording pass. Returns (text, source); falls back to the input on any problem."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return markdown, "unchanged (no API key)"
    try:
        import anthropic

        msg = anthropic.Anthropic().messages.create(
            model=os.environ.get("CLAUDE_MODEL", DEFAULT_MODEL),
            max_tokens=1200,
            system=POLISH_PROMPT,
            messages=[{"role": "user", "content": markdown}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()
    except Exception:
        return markdown, "unchanged (LLM error)"
    if text and numbers_preserved(markdown, text):
        return text, "llm"
    return markdown, "unchanged (guardrail rejected the edit)"
