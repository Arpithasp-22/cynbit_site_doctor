"""Explainable website checks.

Each check reads the crawled `Site` and returns `Issue`s. An issue always says what was found,
why it matters, how to fix it, where it happens, and how sure we are. Checks that need real
HTML are skipped (and reported as skipped) when only a text snapshot is available.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from difflib import SequenceMatcher

from proofkit.claims import audit_page

from .crawler import DATA_DIR, Site
from .extract import Page

SEV_WEIGHT = {"high": 10, "medium": 5, "low": 2}
EFFORT_WEIGHT = {"S": 1, "M": 2, "L": 3}
EFFORT_LABEL = {"S": "under an hour", "M": "a few hours", "L": "days"}
CATEGORIES = ["Trust & proof", "Content", "Conversion", "Search (SEO)", "Accessibility", "Technical hygiene"]

OFFER_KEYWORDS = ("service", "product", "pricing", "solution", "program", "course", "bitelevate", "plan", "path")
NON_OFFER = ("blog", "case-stud", "post", "career", "team", "contact", "story", "diaries")
EXEMPT_THIN = ("contact", "privacy", "terms", "cookies", "careers", "search")


@dataclass
class Issue:
    id: str
    category: str
    title: str
    severity: str  # high | medium | low
    effort: str  # S | M | L
    why: str
    fix: str
    pages: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    source: str = "html"  # html | text | observed
    confidence: str = "confirmed"  # confirmed | likely | verify

    @property
    def priority(self) -> float:
        return SEV_WEIGHT[self.severity] / EFFORT_WEIGHT[self.effort]

    @property
    def quick_win(self) -> bool:
        return self.severity in ("high", "medium") and self.effort == "S"


@dataclass
class Result:
    issues: list[Issue]
    skipped: list[str]
    checked: set[str]


def _ok(site: Site, markup: bool = True) -> list[Page]:
    return [p for p in site.pages if p.status < 400 and (p.has_markup or not markup)]


def _is_offer(p: Page) -> bool:
    path = p.path.lower()
    return any(k in path for k in OFFER_KEYWORDS) and not any(k in path for k in NON_OFFER)


def _paths(pages) -> list[str]:
    return [p.path for p in pages]


# ------------------------------------------------------------------ search (SEO)
def check_titles(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    missing = [p for p in pages if not p.title]
    if missing:
        out.append(Issue("title-missing", "Search (SEO)", "Pages with no title tag", "high", "S",
                         "The title is the headline in Google results and the browser tab.",
                         "Add a unique <title> of 30-60 characters that names the page's topic first.",
                         _paths(missing)))
    bad = [(p, len(p.title)) for p in pages if p.title and (len(p.title) > 65 or len(p.title) < 20)]
    if bad:
        out.append(Issue("title-length", "Search (SEO)", "Page titles too long or too short", "medium", "S",
                         "Google cuts titles near 60 characters; very short titles waste the space.",
                         "Rewrite to 30-60 characters, topic first, brand last. See the Fix Pack for drafts.",
                         [p.path for p, _ in bad], [f"{p.path}: {n} characters" for p, n in bad[:5]]))
    dup = []
    for p in pages:
        if p.title:
            segs = [s.strip().lower() for s in re.split(r"\s[|\-–—•]\s", p.title)]
            if len(segs) != len(set(segs)):
                dup.append(p)
    if dup:
        out.append(Issue("title-brand-dup", "Search (SEO)", "Brand name repeated inside the title", "low", "S",
                         "Looks like a template adds the brand twice, which wastes title space.",
                         "Remove the duplicate suffix in the page template.", _paths(dup),
                         [d.title for d in dup[:3]]))
    return out


def check_meta(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    missing = [p for p in pages if not p.meta_description]
    if missing:
        out.append(Issue("meta-missing", "Search (SEO)", "Pages with no meta description", "medium", "S",
                         "Search engines show this text under the title; without it they pick random text.",
                         "Write a 70-160 character summary per page. See the Fix Pack for drafts.", _paths(missing)))
    odd = [p for p in pages if p.meta_description and not (50 <= len(p.meta_description) <= 170)]
    if odd:
        out.append(Issue("meta-length", "Search (SEO)", "Meta descriptions too short or too long", "low", "S",
                         "Long descriptions are cut off; very short ones say too little.",
                         "Aim for roughly 70-160 characters.", _paths(odd),
                         [f"{p.path}: {len(p.meta_description)} characters" for p in odd[:5]]))
    groups: dict[str, list[Page]] = defaultdict(list)
    for p in pages:
        if p.meta_description:
            groups[p.meta_description.strip().lower()].append(p)
    dups = [ps for ps in groups.values() if len(ps) >= 2]
    if dups:
        affected = [p for ps in dups for p in ps]
        out.append(Issue("meta-duplicate", "Search (SEO)", "Several pages share the same meta description", "medium", "S",
                         "Identical descriptions make different pages look the same in search results.",
                         "Give each page its own description.", _paths(affected),
                         [f'"{ps[0].meta_description[:70]}..." on {len(ps)} pages' for ps in dups[:3]]))
    return out


def check_headings(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    bad = [p for p in pages if len(p.h1) != 1]
    if bad:
        out.append(Issue("h1-count", "Search (SEO)", "Pages without exactly one main heading (H1)", "medium", "S",
                         "One H1 tells search engines and screen readers what the page is about.",
                         "Use a single H1 that states the page topic.", _paths(bad),
                         [f"{p.path}: {len(p.h1)} H1 tags" for p in bad[:5]]))
    skips = []
    for p in pages:
        prev = 0
        for lvl, _ in p.headings:
            if prev and lvl > prev + 1:
                skips.append(p)
                break
            prev = lvl
    if skips:
        out.append(Issue("heading-skip", "Accessibility", "Heading levels skip (for example H2 straight to H4)", "low", "S",
                         "Screen-reader users navigate by heading level; skipped levels confuse the outline.",
                         "Keep levels in order and style with CSS instead.", _paths(skips)))
    return out


def check_head_tags(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    no_canon = [p for p in pages if not p.canonical]
    if no_canon:
        out.append(Issue("canonical", "Search (SEO)", "Pages without a canonical link", "low", "S",
                         "Without it, duplicate URLs (tracking parameters, www vs non-www) can split ranking.",
                         'Add <link rel="canonical"> pointing at the preferred URL.', _paths(no_canon)))
    no_og = [p for p in pages if not all(k in p.og for k in ("og:title", "og:description", "og:image"))]
    if no_og:
        out.append(Issue("open-graph", "Search (SEO)", "Incomplete social-share tags (Open Graph)", "low", "S",
                         "Links shared on LinkedIn or WhatsApp show a weak preview without them.",
                         "Add og:title, og:description and a page-specific og:image.", _paths(no_og)))
    if pages and not any(p.jsonld_types for p in pages):
        out.append(Issue("structured-data", "Search (SEO)", "No structured data (JSON-LD) anywhere", "medium", "M",
                         "Structured data helps search engines show rich results (organisation, FAQ, articles).",
                         "Add Organization on the home page, Article on blog posts, FAQPage where FAQs exist.",
                         ["/"], confidence="confirmed"))
    return out


def check_site_files(site: Site) -> list[Issue]:
    out = []
    if site.kind != "live":
        return out
    if site.robots_txt is None:
        out.append(Issue("robots", "Search (SEO)", "No robots.txt found", "low", "S",
                         "Crawlers look for it first; it also advertises your sitemap.",
                         "Add /robots.txt with a Sitemap: line.", ["/"]))
    if not site.sitemap_urls:
        out.append(Issue("sitemap", "Search (SEO)", "No XML sitemap found", "medium", "S",
                         "A sitemap helps search engines discover every page, including new blog posts.",
                         "Generate /sitemap.xml and list it in robots.txt.", ["/"]))
    return out


def check_broken_links(site: Site) -> list[Issue]:
    if not site.broken_links:
        return []
    sev = "high" if len(site.broken_links) >= 3 else "medium"
    return [Issue("broken-links", "Technical hygiene", "Broken internal links or pages", sev, "S",
                  "Visitors and search engines hit dead ends, which lowers trust and rankings.",
                  "Fix or redirect each URL, or remove the link.", sorted({b[0] for b in site.broken_links}),
                  [f"{b[1]} returned {b[2] or 'no response'} (linked from {b[0]})" for b in site.broken_links[:6]])]


# ------------------------------------------------------------------ accessibility
def check_icons(site: Site) -> list[Issue]:
    leaks = [p for p in _ok(site) if p.icon_leaks]
    if not leaks:
        return []
    names = sorted({n for p in leaks for n in p.icon_leaks})
    return [Issue("icon-text", "Accessibility", "Icon names are exposed as text", "medium", "S",
                  "Icon fonts store icons as words such as 'expand_more'. Screen readers read them aloud, and if "
                  "the font fails to load visitors see the raw words glued to labels.",
                  'Add aria-hidden="true" to every icon element (or swap to inline SVG icons).',
                  _paths(leaks), [", ".join(names[:8])])]


def check_images(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    no_alt = [(p, sum(1 for i in p.images if i.alt is None)) for p in pages]
    no_alt = [(p, n) for p, n in no_alt if n]
    if no_alt:
        out.append(Issue("img-alt-missing", "Accessibility", "Images with no alt attribute", "medium", "S",
                         "Screen readers cannot describe them and search engines cannot index them.",
                         'Add alt text describing the image, or alt="" for purely decorative images.',
                         [p.path for p, _ in no_alt], [f"{p.path}: {n} image(s)" for p, n in no_alt[:5]]))
    weak = []
    for p in pages:
        label = (p.h1[0] if p.h1 else p.title or "").strip().lower()
        if label and any((i.alt or "").strip().lower() == label for i in p.images):
            weak.append(p)
    if weak:
        out.append(Issue("img-alt-weak", "Accessibility", "Image alt text just repeats the page title", "low", "S",
                         "Alt text should describe what the picture shows, not repeat the heading.",
                         "Rewrite the alt text to describe the image.", _paths(weak)))
    unsized = [(p, sum(1 for i in p.images if not i.has_dims)) for p in pages]
    unsized = [(p, n) for p, n in unsized if n >= 5]
    if unsized:
        out.append(Issue("img-dims", "Technical hygiene", "Many images have no width and height", "low", "M",
                         "The page jumps around while loading (layout shift), which hurts experience and Core Web Vitals.",
                         "Set width and height (or aspect-ratio) on images.", [p.path for p, _ in unsized]))
    return out


def check_forms(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    unlabelled = []
    for p in pages:
        n = sum(1 for f in p.forms for fld in f.fields if not fld.labelled)
        if n:
            unlabelled.append((p, n))
    if unlabelled:
        out.append(Issue("form-labels", "Accessibility", "Form fields without a proper label", "medium", "S",
                         "A placeholder disappears when typing and is not a reliable label for screen readers.",
                         "Add a visible <label for=...> or aria-label to every field.",
                         [p.path for p, _ in unlabelled], [f"{p.path}: {n} field(s)" for p, n in unlabelled[:5]]))
    return out


def check_page_basics(site: Site) -> list[Issue]:
    pages, out = _ok(site), []
    no_lang = [p for p in pages if not p.lang]
    if no_lang:
        out.append(Issue("lang", "Accessibility", "Missing language attribute on <html>", "medium", "S",
                         "Screen readers use it to choose the right pronunciation.",
                         'Add lang="en" to the <html> tag.', _paths(no_lang)))
    no_vp = [p for p in pages if not p.viewport]
    if no_vp:
        out.append(Issue("viewport", "Technical hygiene", "Missing mobile viewport tag", "high", "S",
                         "Without it phones show a shrunken desktop page.",
                         'Add <meta name="viewport" content="width=device-width, initial-scale=1">.', _paths(no_vp)))
    return out


def check_link_text(site: Site) -> list[Issue]:
    vague = re.compile(r"^(read more|read entry|click here|learn more|view details|here|more)$", re.I)
    bad = []
    for p in _ok(site):
        c = Counter(l.text.strip().lower() for l in p.links if vague.match(l.text.strip()))
        top = [(t, n) for t, n in c.items() if n >= 3]
        if top:
            bad.append((p, top))
    if not bad:
        return []
    return [Issue("link-text", "Accessibility", "Repeated vague link text", "low", "S",
                  "Screen-reader users hear a list of identical links ('View details' x20) with no context.",
                  "Make each link say where it goes, or add a visually hidden suffix with the item name.",
                  [p.path for p, _ in bad], [f"{p.path}: '{t}' x{n}" for p, top in bad[:3] for t, n in top])]


# ------------------------------------------------------------------ conversion
def check_anchors(site: Site) -> list[Issue]:
    bad = [p for p in _ok(site) if p.anchors_missing]
    if not bad:
        return []
    return [Issue("anchor-missing", "Conversion", "Buttons point to a spot on the page that does not exist", "medium", "S",
                  "A visitor clicks, nothing happens, and the enquiry is lost.",
                  "Make the target id exist on the page, or link to the contact form page.", _paths(bad),
                  [f"{p.path}: {', '.join(p.anchors_missing[:3])}" for p in bad[:4]])]


def check_inquiry(site: Site) -> list[Issue]:
    out = []
    contact = [p for p in _ok(site) if "contact" in p.path.lower()]
    for p in contact:
        inquiry = [f for f in p.forms if f.is_inquiry]
        if not inquiry:
            out.append(Issue("no-inquiry-form", "Conversion", "Contact page has no inquiry form", "high", "M",
                             "Many visitors will not phone or open an email app; a form captures them.",
                             "Add a short form (name, email, what you need) with a clear confirmation message.", [p.path]))
        elif all(not fld.required for f in inquiry for fld in f.fields):
            out.append(Issue("form-required", "Conversion", "Inquiry form marks no field as required", "medium", "S",
                             "Visitors cannot tell what is mandatory, and empty submissions can slip through.",
                             "Mark name, email and message as required and show inline errors.", [p.path],
                             confidence="verify"))
    offers = [p for p in _ok(site) if _is_offer(p) and not p.ctas]
    if offers:
        out.append(Issue("offer-no-cta", "Conversion", "Offer pages with no call to action", "medium", "S",
                         "A visitor who is convinced has nothing to click.",
                         "Add one clear primary action per offer page.", _paths(offers)))
    return out


def check_contact_info(site: Site) -> list[Issue]:
    pages = _ok(site)
    phones = {ph for p in pages for ph in p.phones}
    out = []
    if len(phones) >= 3:
        out.append(Issue("phones", "Conversion", f"{len(phones)} different phone numbers with no stated purpose", "low", "S",
                         "Visitors do not know which number is sales, support or hiring, or when it is answered.",
                         "Label each number and add opening hours.", ["/"], confidence="confirmed"))
    return out


# ------------------------------------------------------------------ trust & content
def check_claims(site: Site) -> list[Issue]:
    seen: dict[str, tuple[str, object]] = {}
    for p in site.pages:
        for f in audit_page(p.main_text):
            if f.severity in ("high", "medium"):
                seen.setdefault(f.text.lower(), (p.path, f))
    if not seen:
        return []
    items = list(seen.values())
    n_high = sum(1 for _, f in items if f.severity == "high")
    sev = "high" if n_high >= 3 else "medium"
    return [Issue("claims", "Trust & proof", f"{len(items)} claims give the reader no period, baseline or source", sev, "M",
                  "Unsupported numbers invite doubt, and absolute claims ('100%') are hard to defend. "
                  "Buyers who cannot check a claim discount it.",
                  "For each number add: the period measured, what it improved from, and how it was measured. "
                  "The Fix Pack lists a rewrite request per claim.",
                  sorted({path for path, _ in items}),
                  [f'"{f.text[:70]}" ({path}): {", ".join(f.issues)}' for path, f in items[:6]],
                  source="text", confidence="confirmed")]


PLACEHOLDER = re.compile(
    r"lorem ipsum|\bcoming soon\b|\bTBD\b|\bTODO\b|system ready|runtime active|\bactive now\b|<user>|sample text", re.I)


def check_placeholders(site: Site) -> list[Issue]:
    hits, pages = [], set()
    for p in site.pages:
        for m in PLACEHOLDER.finditer(p.main_text):
            hits.append(f'"{m.group(0)}" on {p.path}')
            pages.add(p.path)
    if not hits:
        return []
    return [Issue("placeholder", "Content", "Placeholder or decorative status text that reads like live data", "low", "S",
                  "Labels such as 'System Ready' or 'Active now' look like real monitoring data; if they are decoration "
                  "visitors may feel misled.",
                  "Remove them, or connect them to real data and say where it comes from.",
                  sorted(pages), hits[:5], source="text", confidence="likely")]


def check_thin(site: Site) -> list[Issue]:
    thin_offer, thin_other = [], []
    for p in _ok(site):
        if any(k in p.path.lower() for k in EXEMPT_THIN) or p.path == "/":
            continue
        if _is_offer(p) and p.word_count < 300:
            thin_offer.append(p)
        elif p.word_count < 120:
            thin_other.append(p)
    out = []
    if thin_offer:
        out.append(Issue("thin-offer", "Content", "Offer pages with very little content", "medium", "M",
                         "Buyers compare pages; a few lines per service gives them nothing to compare or trust.",
                         "Per service: who it is for, what is delivered, how it works, typical timeline, an example.",
                         _paths(thin_offer), [f"{p.path}: {p.word_count} words" for p in thin_offer[:5]]))
    if thin_other:
        out.append(Issue("thin-other", "Content", "Pages with very little text", "low", "M",
                         "Thin pages rarely rank and rarely persuade.",
                         "Add substance or merge the page into a stronger one.", _paths(thin_other),
                         [f"{p.path}: {p.word_count} words" for p in thin_other[:5]]))
    return out


def check_duplicate_blocks(site: Site) -> list[Issue]:
    bad = [p for p in _ok(site) if p.duplicate_blocks]
    if not bad:
        return []
    return [Issue("dup-blocks", "Content", "The same text block appears twice on a page", "medium", "S",
                  "Usually a layout bug (for example a repeated testimonial strip). It makes the page look padded "
                  "and inflates counts such as '14 reviews'.",
                  "Render each block once.", _paths(bad),
                  [f'{p.path}: {len(p.duplicate_blocks)} repeated block(s), e.g. "{p.duplicate_blocks[0][:60]}..."' for p in bad[:3]])]


def check_near_duplicates(site: Site) -> list[Issue]:
    pages = [p for p in _ok(site) if p.word_count >= 80]
    if len(pages) < 2:
        return []
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    sims = cosine_similarity(TfidfVectorizer(stop_words="english").fit_transform([p.main_text for p in pages]))
    pairs = [(pages[i], pages[j], sims[i][j]) for i in range(len(pages)) for j in range(i + 1, len(pages))
             if sims[i][j] >= 0.92]
    if not pairs:
        return []
    return [Issue("near-dup", "Content", "Pages that are almost identical", "low", "M",
                  "Search engines may pick one and ignore the other.", "Merge them, or make each distinct.",
                  sorted({p.path for a, b, _ in pairs for p in (a, b)}),
                  [f"{a.path} and {b.path}: {s:.0%} similar" for a, b, s in pairs[:4]])]


def check_dated(site: Site) -> list[Issue]:
    bad, old = [], []
    for p in site.pages:
        if not p.published or not p.title:
            continue
        m = re.match(r"(\d{4})", p.published)
        if not m:
            continue
        year = int(m.group(1))
        years = [int(y) for y in re.findall(r"\b(20\d\d)\b", p.title + " " + " ".join(p.h1))]
        if years and max(years) > year:
            bad.append(f"{p.path}: published {p.published[:10]} but the title says {max(years)}")
        elif year <= date.today().year - 2:
            old.append(p)
    out = []
    if bad:
        out.append(Issue("date-mismatch", "Content", "Article date and the year in its title disagree", "medium", "S",
                         "A '2026' article dated 2025 looks careless and confuses freshness signals.",
                         "Align the published date, the title year and the 'last updated' date.",
                         [b.split(":")[0] for b in bad], bad[:4], source="text", confidence="confirmed"))
    if old:
        out.append(Issue("stale", "Content", "Pages not updated for two years or more", "low", "M",
                         "Old pages signal an inactive business.", "Refresh or retire them.", _paths(old), source="text"))
    return out


OFFER_ELEMENTS = {
    "pricing or fees": r"(₹|\brs\.?\s?\d|\$\s?\d|€|\bprice\b|\bpricing\b|per month|/month|free trial|\bplans?\b|\bfee\b)",
    "status (live / beta / coming soon)": r"\b(now live|is live|live now|in beta|\bbeta\b|coming soon|early access|generally available|available now)\b",
    "demo, trial or sign-up": r"\b(demo|book a|schedule a|request a|free trial|try (it|now|free)|regist\w+|sign up|enrol\w*|apply now|claim your)\b",
    "named proof (case study, rating, review)": r"\b(case stud|testimonial|trusted by|rated|rating|reviews?)\b",
    "how it works / process": r"\b(how it works|process|steps?|phase|curriculum|timeline)\b",
    "FAQ": r"\b(faq|frequently asked)\b",
}


def offer_gaps(page: Page) -> list[str]:
    return [name for name, pat in OFFER_ELEMENTS.items() if not re.search(pat, page.main_text, re.I)]


def check_offer_pages(site: Site) -> list[Issue]:
    rows = [(p, offer_gaps(p)) for p in _ok(site, markup=False) if _is_offer(p)]
    rows = [(p, g) for p, g in rows if g]
    if not rows:
        return []
    worst = max(len(g) for _, g in rows)
    return [Issue("offer-gaps", "Content", "Offer pages are missing what a buyer looks for", "high" if worst >= 4 else "medium", "M",
                  "Before contacting anyone, buyers look for price signals, availability, a way to try it, proof and "
                  "answers to common questions. If the page does not answer, they leave or ask a competitor.",
                  "Fill each gap or state clearly that it is by quote. See the checklist in the Fix Pack.",
                  _paths([p for p, _ in rows]), [f"{p.path}: missing {', '.join(g)}" for p, g in rows[:6]],
                  source="text", confidence="likely")]


def check_spelling(site: Site) -> list[Issue]:
    try:
        from spellchecker import SpellChecker
    except ImportError:
        return []
    allow = {w.strip().lower() for w in (DATA_DIR / "spell_allow.txt").read_text(encoding="utf-8").splitlines() if w.strip()}
    spell = SpellChecker()
    counts: Counter = Counter()
    where: dict[str, str] = {}
    for p in site.pages:
        for w in re.findall(r"\b[A-Za-z]{5,}\b", p.main_text):
            if w.isupper() or any(c.isupper() for c in w[1:]):
                continue
            lw = w.lower()
            counts[lw] += 1
            where.setdefault(lw, p.path)
    found = []
    for w, n in counts.items():
        if n > 2 or w in allow:
            continue
        if spell.unknown([w]):
            fix = spell.correction(w)
            if fix and fix != w and SequenceMatcher(None, w, fix).ratio() >= 0.85:
                found.append((w, fix, where[w]))
    if not found:
        return []
    return [Issue("spelling", "Content", "Possible spelling mistakes", "low", "S",
                  "Typos undermine credibility, especially on a page about quality and rigour.",
                  "Review each suggestion; ignore product or place names.", sorted({p for _, _, p in found}),
                  [f"'{w}' on {p}: did you mean '{f}'?" for w, f, p in found[:8]], source="text", confidence="verify")]


# ------------------------------------------------------------------ technical hygiene
def check_https_headers(site: Site) -> list[Issue]:
    if site.kind != "live":
        return []
    out = []
    host = site.base_url.split("//")[-1].split("/")[0]
    local = host.startswith(("localhost", "127.", "0.0.0.0"))
    if site.base_url.startswith("http://") and not local:
        out.append(Issue("https", "Technical hygiene", "Site is served over plain HTTP", "high", "M",
                         "Browsers warn visitors and search engines rank secure sites higher.",
                         "Install a certificate and redirect all HTTP to HTTPS.", ["/"]))
    pages = _ok(site)
    if pages and not local:
        missing = [h for h in ("strict-transport-security", "x-content-type-options", "content-security-policy")
                   if not any(h in p.headers for p in pages)]
        if missing:
            out.append(Issue("sec-headers", "Technical hygiene", "Standard security headers are missing", "low", "S",
                             "These headers are a cheap defence against common attacks and are checked in security reviews.",
                             "Set " + ", ".join(missing) + " at the host or CDN.", ["/"], confidence="confirmed"))
    return out


# ------------------------------------------------------------------ registry
# (label, function, needs_markup, categories it can score)
CHECKS = [
    ("Page titles", check_titles, True, ["Search (SEO)"]),
    ("Meta descriptions", check_meta, True, ["Search (SEO)"]),
    ("Headings", check_headings, True, ["Search (SEO)", "Accessibility"]),
    ("Canonical, social tags, structured data", check_head_tags, True, ["Search (SEO)"]),
    ("robots.txt and sitemap", check_site_files, True, ["Search (SEO)"]),
    ("Broken links", check_broken_links, True, ["Technical hygiene"]),
    ("Icon text exposed to screen readers", check_icons, True, ["Accessibility"]),
    ("Image alt text and sizes", check_images, True, ["Accessibility", "Technical hygiene"]),
    ("Form labels", check_forms, True, ["Accessibility"]),
    ("Language and mobile viewport", check_page_basics, True, ["Accessibility", "Technical hygiene"]),
    ("Link text", check_link_text, True, ["Accessibility"]),
    ("Buttons that point nowhere", check_anchors, True, ["Conversion"]),
    ("Inquiry form and calls to action", check_inquiry, True, ["Conversion"]),
    ("Contact details", check_contact_info, True, ["Conversion"]),
    ("Unsupported claims", check_claims, False, ["Trust & proof"]),
    ("Placeholder text", check_placeholders, False, ["Content"]),
    ("Thin pages", check_thin, True, ["Content"]),
    ("Repeated blocks", check_duplicate_blocks, True, ["Content"]),
    ("Near-duplicate pages", check_near_duplicates, True, ["Content"]),
    ("Dated content", check_dated, False, ["Content"]),
    ("What offer pages are missing", check_offer_pages, False, ["Content"]),
    ("Spelling", check_spelling, False, ["Content"]),
    ("HTTPS and security headers", check_https_headers, True, ["Technical hygiene"]),
]


def observed_issues(site: Site) -> list[Issue]:
    return [Issue(o["id"], o["category"], o["title"], o["severity"], o["effort"], o["why"], o["fix"],
                  o.get("pages", []), o.get("evidence", []), source="observed", confidence=o.get("confidence", "likely"))
            for o in site.observations]


def run_checks(site: Site) -> Result:
    issues: list[Issue] = []
    skipped: list[str] = []
    checked: set[str] = set()
    has_markup = any(p.has_markup for p in site.pages)
    for label, fn, needs_markup, cats in CHECKS:
        if needs_markup and not has_markup:
            skipped.append(label)
            continue
        issues.extend(fn(site))
        checked.update(cats)
    if site.observations:
        issues.extend(observed_issues(site))
        checked.update(o["category"] for o in site.observations)
    order = {"high": 0, "medium": 1, "low": 2}
    issues.sort(key=lambda i: (-i.priority, order[i.severity], -len(i.pages)))
    return Result(issues, skipped, checked)
