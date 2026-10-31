"""Turn findings into ready-to-use fixes: rewrites, checklists, evidence requests, one Fix Pack file."""
from __future__ import annotations

import re

from proofkit.casestudy import numbers_preserved
from proofkit.claims import audit_page

from .checks import OFFER_ELEMENTS, Result, _is_offer
from .crawler import Site
from .extract import Page
from .secrets import get_secret, has_api_key, get_model


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut + "…"


def suggest_title(page: Page, brand: str) -> str:
    """Topic first, brand last, at most 60 characters."""
    topic = (page.h1[0] if page.h1 else (page.title or page.path.strip("/").replace("-", " ").title() or "Home"))
    topic = re.split(r"\s[|–—]\s", topic)[0].strip()
    if page.path == "/":
        return _clip(f"{brand}: {topic}", 60)
    room = 60 - len(brand) - 3
    return f"{_clip(topic, max(room, 15))} | {brand}"


def suggest_meta(page: Page) -> str:
    """Extractive draft: the first informative sentences of the page, 70-155 characters."""
    sentences = re.split(r"(?<=[.!?])\s+", page.main_text.replace("\n", " "))
    sentences = [s.strip() for s in sentences if len(s.split()) >= 6 and "@" not in s]
    out = ""
    for s in sentences:
        if len(out) + len(s) + 1 > 155:
            break
        out = (out + " " + s).strip()
        if len(out) >= 90:
            break
    return out or _clip(sentences[0], 155) if sentences else ""


def polish_meta(draft: str) -> tuple[str, str]:
    """Optional LLM rewrite. Rejected unless it keeps every number and stays within 160 characters."""
    if not draft or not has_api_key():
        return draft, "extractive"
    try:
        import anthropic

        msg = anthropic.Anthropic(api_key=get_secret("ANTHROPIC_API_KEY")).messages.create(
            model=get_model(), max_tokens=120,
            system="Rewrite the text as one meta description of 120-155 characters for a web page. Use only facts in "
                   "the text. Do not add numbers, claims or superlatives. Output the description only.",
            messages=[{"role": "user", "content": draft}])
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip().strip('"')
    except Exception:
        return draft, "extractive"
    if text and len(text) <= 160 and numbers_preserved(draft, text):
        return text, "llm"
    return draft, "extractive (LLM edit rejected)"


def title_meta_rows(site: Site, brand: str) -> list[dict]:
    rows = []
    for p in site.pages:
        if p.status >= 400:
            continue
        new_title, new_meta = suggest_title(p, brand), suggest_meta(p)
        rows.append({
            "Page": p.path, "Current title": p.title or "(none)", "Suggested title": new_title,
            "Title length": len(new_title), "Current description": p.meta_description or "(none)" if p.has_markup else "(not captured)",
            "Suggested description": new_meta, "Description length": len(new_meta),
        })
    return rows


def claim_requests(site: Site) -> list[dict]:
    seen, rows = set(), []
    for p in site.pages:
        for f in audit_page(p.main_text):
            if f.severity == "ok" or f.text.lower() in seen:
                continue
            seen.add(f.text.lower())
            if "no coverage detail" in f.issues:
                template = "24/7 support by [channels], with a first response within [X hours] (see our support policy)."
            elif "vague superlative, not measurable" in f.issues and len(f.issues) == 1:
                template = "Replace with one specific, checkable fact, e.g. '[what you did] for [N] clients since [year]'."
            else:
                template = ("[Metric] changed from [BASELINE] to [VALUE] over [PERIOD], measured by [TOOL OR REPORT]. "
                            "Client: [NAME, with permission].")
            rows.append({"Page": p.path, "Claim as written": _clip(f.text, 110), "Priority": f.severity,
                         "What is missing": "; ".join(f.issues), "Ask for": f.suggestion, "Rewrite template": template})
    return rows


def offer_checklist(site: Site) -> list[dict]:
    rows = []
    for p in site.pages:
        if p.status < 400 and _is_offer(p):
            row = {"Page": p.path}
            for name, pat in OFFER_ELEMENTS.items():
                row[name] = "yes" if re.search(pat, p.main_text, re.I) else "MISSING"
            rows.append(row)
    return rows


CONFIRMATION = (
    "Thanks, {name}. We have your message and a real person will reply within [1 business day, Mon-Sat, IST]. "
    "Meanwhile you can [see our case studies / read the FAQ]. Reference: #[ID]."
)


def contact_form_spec(site: Site) -> str:
    detected = None
    for p in site.pages:
        for f in p.forms:
            if f.is_inquiry:
                detected = (p.path, f)
    lines = ["## Recommended inquiry form", ""]
    if detected:
        path, form = detected
        have = ", ".join(f"{f.name}{' (required)' if f.required else ''}" for f in form.fields)
        lines += [f"Detected on `{path}`: {have}.", ""]
    lines += [
        "| Field | Required | Why |", "|---|---|---|",
        "| Full name | yes | Personalised reply |", "| Work email | yes | The reply channel |",
        "| What do you need? (select: AI automation / Software / Cloud / Marketing / BitElevate / Other) | yes | Routes to the right person |",
        "| Message | yes | Context for the first reply |", "| Company | optional | Qualifies the lead |",
        "| Budget range and timeline | optional | Lets the team prioritise |",
        "| Consent checkbox for contact and data use | yes | Data-protection hygiene |", "",
        "**Confirmation message (shown on screen and emailed):**", "", f"> {CONFIRMATION}", "",
        "**Also:** label each phone number (sales, support, hiring), show opening hours, and point sales enquiries "
        "to a sales address instead of `opportunities@`.",
    ]
    return "\n".join(lines)


def fix_pack_markdown(site: Site, result: Result, brand: str = "Cynbit") -> str:
    out = [f"# Fix Pack for {site.base_url}", "",
           f"Generated from a {'live scan' if site.kind == 'live' else 'text snapshot'} on {site.fetched_at[:10]}. "
           "Every item says where it applies; drafts need a human to approve them before publishing.", "",
           "## 1. Prioritised issues", ""]
    for n, i in enumerate(result.issues, 1):
        out += [f"### {n}. {i.title}", f"*{i.category} | {i.severity} priority | effort: {i.effort} | confidence: {i.confidence} | source: {i.source}*", "",
                f"**Why it matters:** {i.why}", "", f"**Fix:** {i.fix}", ""]
        if i.pages:
            out.append("**Where:** " + ", ".join(f"`{p}`" for p in i.pages[:8]))
        if i.evidence:
            out += ["", "**Evidence:**"] + [f"- {e}" for e in i.evidence[:6]]
        out.append("")
    claims = claim_requests(site)
    if claims:
        out += ["## 2. Claims to back up", "", "| Page | Claim | Missing | Rewrite template |", "|---|---|---|---|"]
        out += [f"| {c['Page']} | {c['Claim as written']} | {c['What is missing']} | {c['Rewrite template']} |" for c in claims]
        out.append("")
    offers = offer_checklist(site)
    if offers:
        cols = list(offers[0].keys())
        out += ["## 3. What each offer page is missing", "", "| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        out += ["| " + " | ".join(r[c] for c in cols) + " |" for r in offers]
        out.append("")
    if any(p.has_markup for p in site.pages):
        out += ["## 4. Title and description drafts", "", "| Page | Suggested title | Suggested description |", "|---|---|---|"]
        out += [f"| {r['Page']} | {r['Suggested title']} | {r['Suggested description']} |" for r in title_meta_rows(site, brand)]
        out.append("")
    out += [contact_form_spec(site), ""]
    return "\n".join(out)
