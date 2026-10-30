"""Claim auditor.

Finds numeric and vague marketing claims in text and checks whether each one carries the
three things a reader needs to believe it: a time period, a baseline to compare against,
and a source. It does NOT decide whether a claim is true. It flags claims that cannot be
checked from the page itself, and suggests what to add.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

NUMBER_PATTERNS = {
    "percent": re.compile(r"[+-]?\d+(?:\.\d+)?\s?%"),
    "multiplier": re.compile(r"\b\d+(?:\.\d+)?\s?x\b", re.I),
    "count": re.compile(r"\b\d[\d,]*(?:\.\d+)?\s?[km]?\+", re.I),
    "always_on": re.compile(r"\b24\s?/\s?7\b"),
}
ABSOLUTE = re.compile(r"(?<![\d.])100\s?%")
VAGUE_TERMS = [
    "revolutionary", "premier", "world-class", "globally recognized", "globally recognised",
    "zero friction", "best-in-class", "industry-leading", "unparalleled", "cutting-edge",
]

TIMEFRAME = re.compile(
    r"\b(?:20\d\d|q[1-4])\b|\b\d+\s*(?:day|week|month|year)s?\b|\b(?:since|between|during)\b", re.I
)
BASELINE = re.compile(
    r"\b(?:from|vs\.?|versus|compared (?:to|with)|baseline|before|previously|up from|down from)\b", re.I
)
SOURCE = re.compile(r"\b(?:source|according to|audited|measured (?:by|in|using)|verified)\b|https?://", re.I)

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "ok": 3}


@dataclass
class Finding:
    id: str
    text: str
    client: str | None
    kinds: list[str]
    issues: list[str] = field(default_factory=list)
    severity: str = "ok"
    suggestion: str = ""


def _kinds(text: str) -> list[str]:
    found = [name for name, pat in NUMBER_PATTERNS.items() if pat.search(text)]
    if ABSOLUTE.search(text):
        found.append("absolute")
    lowered = text.lower()
    if any(term in lowered for term in VAGUE_TERMS):
        found.append("vague")
    return found


def audit_claim(claim_id: str, text: str, client: str | None = None, extra_context: str = "") -> Finding:
    """Audit one claim. `extra_context` carries structured fields (source, period) if known."""
    kinds = _kinds(text)
    context = f"{text} {extra_context}"
    issues: list[str] = []

    measured = any(k in kinds for k in ("percent", "multiplier", "count", "absolute"))
    if measured:
        if not TIMEFRAME.search(context):
            issues.append("no time period")
        if not BASELINE.search(context):
            issues.append("no baseline")
        if not SOURCE.search(context):
            issues.append("no source")
    elif "always_on" in kinds:
        # A coverage promise has no baseline or period; the useful question is what it covers.
        if not re.search(r"\b(?:sla|response|within|channels?|email|phone|chat|hours?)\b", context, re.I):
            issues.append("no coverage detail")
    if "absolute" in kinds:
        issues.append("absolute claim (100%) is hard to defend")
    if "vague" in kinds:
        issues.append("vague superlative, not measurable")

    if "absolute" in kinds or len(issues) >= 3:
        severity = "high"
    elif len(issues) == 2:
        severity = "medium"
    elif len(issues) == 1:
        severity = "low"
    else:
        severity = "ok"

    suggestion = ""
    if issues:
        parts = []
        if "no time period" in issues:
            parts.append("the period measured")
        if "no baseline" in issues:
            parts.append("what it improved from")
        if "no source" in issues:
            parts.append("how it was measured (tool or report)")
        suggestion = "Add " + ", ".join(parts) + "." if parts else ""
        if "no coverage detail" in issues:
            suggestion = "State what 24/7 covers: channels and the response-time commitment (SLA)."
        if "vague superlative, not measurable" in issues:
            suggestion = (suggestion + " Replace the superlative with a specific, checkable fact.").strip()
        if "absolute claim (100%) is hard to defend" in issues:
            suggestion = (suggestion + " Say what was counted, e.g. '12 of 12 milestones delivered on time'.").strip()

    return Finding(claim_id, text, client, kinds, issues, severity, suggestion)


def load_site_claims() -> list[dict]:
    with open(DATA_DIR / "site_claims.json", encoding="utf-8") as fh:
        return json.load(fh)["claims"]


def audit_claims(claims: list[dict]) -> list[Finding]:
    findings = [
        audit_claim(c["id"], c["text"], c.get("client"),
                    " ".join(str(c.get(k, "")) for k in ("source", "period", "baseline")))
        for c in claims
    ]
    return sorted(findings, key=lambda f: SEVERITY_ORDER[f.severity])


def audit_page(text: str) -> list[Finding]:
    """Scan free text: audit every line or sentence that contains a numeric or vague claim."""
    findings: list[Finding] = []
    n = 0
    for line in text.splitlines():
        for fragment in re.split(r"(?<=[.!?])\s+", line.strip()):
            if fragment and _kinds(fragment):
                n += 1
                findings.append(audit_claim(f"p{n}", fragment))
    return sorted(findings, key=lambda f: SEVERITY_ORDER[f.severity])


def summarise(findings: list[Finding]) -> dict[str, int]:
    counts = {"high": 0, "medium": 0, "low": 0, "ok": 0}
    for f in findings:
        counts[f.severity] += 1
    counts["total"] = len(findings)
    return counts
