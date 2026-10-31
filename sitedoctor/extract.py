"""Turn one page of raw HTML into a structured `Page`.

Everything the checks need is extracted here once, so the checks themselves stay small and
testable. Nothing in this module calls the network.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

ICON_CLASS = re.compile(r"material[-_ ]?(symbols|icons)", re.I)
LIGATURE = re.compile(r"^[a-z]+(?:_[a-z0-9]+)*$")
CTA_TEXT = re.compile(
    r"\b(inquire|enquire|get started|start discovery|start your|contact|book|schedule|request|"
    r"demo|join|apply|subscribe|sign up|try|claim|register|talk to|speak to|audit|generate|send)\b",
    re.I,
)
PHONE = re.compile(r"\+\d{1,3}[\s-]?\d[\d\s-]{8,13}\d")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SECURITY_HEADERS = ("strict-transport-security", "x-content-type-options",
                    "content-security-policy", "x-frame-options")


@dataclass
class Link:
    href: str
    text: str
    internal: bool


@dataclass
class Image:
    src: str
    alt: str | None  # None means the alt attribute is missing; "" means decorative
    has_dims: bool
    lazy: bool


@dataclass
class FormField:
    name: str
    type: str
    required: bool
    labelled: bool


@dataclass
class Form:
    fields: list[FormField]
    submit_text: str

    @property
    def is_inquiry(self) -> bool:
        return any(f.type == "textarea" for f in self.fields)


@dataclass
class Page:
    url: str
    status: int = 200
    has_markup: bool = True  # False for text-only snapshots: markup checks are skipped
    html_bytes: int = 0
    title: str | None = None
    meta_description: str | None = None
    canonical: str | None = None
    lang: str | None = None
    viewport: bool = False
    og: dict[str, str] = field(default_factory=dict)
    h1: list[str] = field(default_factory=list)
    headings: list[list] = field(default_factory=list)  # [[level, text], ...]
    main_text: str = ""
    word_count: int = 0
    links: list[Link] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)
    forms: list[Form] = field(default_factory=list)
    jsonld_types: list[str] = field(default_factory=list)
    icon_leaks: list[str] = field(default_factory=list)
    anchors_missing: list[str] = field(default_factory=list)
    duplicate_blocks: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    ctas: list[str] = field(default_factory=list)
    scripts: int = 0
    published: str | None = None
    headers: dict[str, str] = field(default_factory=dict)

    @property
    def path(self) -> str:
        p = urlparse(self.url).path.rstrip("/")
        return p or "/"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Page":
        d = dict(d)
        d["links"] = [Link(**x) for x in d.get("links", [])]
        d["images"] = [Image(**x) for x in d.get("images", [])]
        d["forms"] = [Form(fields=[FormField(**f) for f in x["fields"]], submit_text=x["submit_text"])
                      for x in d.get("forms", [])]
        return cls(**d)


def norm_host(host: str) -> str:
    host = host.lower()
    return host[4:] if host.startswith("www.") else host


def _text(el) -> str:
    return re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()


def _is_hidden(el) -> bool:
    node = el
    while node is not None and getattr(node, "attrs", None) is not None:
        if str(node.attrs.get("aria-hidden", "")).lower() == "true":
            return True
        node = node.parent
    return False


def _jsonld_types(soup) -> list[str]:
    found: list[str] = []

    def walk(obj):
        if isinstance(obj, list):
            for o in obj:
                walk(o)
        elif isinstance(obj, dict):
            t = obj.get("@type")
            if isinstance(t, str):
                found.append(t)
            elif isinstance(t, list):
                found.extend(str(x) for x in t)
            for v in obj.values():
                if isinstance(v, (list, dict)):
                    walk(v)

    for s in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            walk(json.loads(s.string or s.get_text() or ""))
        except (ValueError, TypeError):
            continue
    return list(dict.fromkeys(found))


def _is_labelled(el, soup, label_for: set[str]) -> bool:
    if el.get("aria-label") or el.get("aria-labelledby") or el.get("title"):
        return True
    if el.get("id") and el["id"] in label_for:
        return True
    return el.find_parent("label") is not None


def parse_html(url: str, html: str, status: int = 200, headers: dict[str, str] | None = None) -> Page:
    soup = BeautifulSoup(html, "html.parser")
    host = norm_host(urlparse(url).netloc)
    headers = {k.lower(): v for k, v in (headers or {}).items()}

    title = _text(soup.title) if soup.title else None
    meta_desc = None
    og: dict[str, str] = {}
    viewport = False
    published = None
    for m in soup.find_all("meta"):
        name = (m.get("name") or "").lower()
        prop = (m.get("property") or "").lower()
        content = (m.get("content") or "").strip()
        if name == "description":
            meta_desc = content
        elif name == "viewport":
            viewport = True
        if prop.startswith("og:") and content:
            og[prop] = content
        if prop == "article:published_time" and content:
            published = content
    if not published:
        t = soup.find("time", attrs={"datetime": True})
        published = t["datetime"] if t else None

    canonical = None
    for l in soup.find_all("link"):
        rel = l.get("rel") or []
        rel = rel if isinstance(rel, list) else [rel]
        if "canonical" in [r.lower() for r in rel]:
            canonical = l.get("href")
            break

    # icon-font ligatures that a screen reader would read aloud ("expand_more")
    leaks: list[str] = []
    for el in soup.find_all(class_=ICON_CLASS):
        txt = el.get_text(strip=True)
        if txt and LIGATURE.match(txt) and not _is_hidden(el):
            leaks.append(txt)

    # links, phones, emails, CTAs come from the whole page (nav and footer included)
    ids = {t["id"] for t in soup.find_all(id=True)} | {t["name"] for t in soup.find_all(attrs={"name": True}) if t.name == "a"}
    links, anchors_missing, phones, emails, ctas = [], [], [], [], []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = _text(a)
        if href.startswith("tel:"):
            phones.append(re.sub(r"\D", "", href))
            continue
        if href.startswith("mailto:"):
            emails.append(href[7:].split("?")[0].lower())
            continue
        if href.startswith("javascript:"):
            continue
        if href.startswith("#"):
            if len(href) > 1 and href[1:] not in ids:
                anchors_missing.append(href)
            continue
        absolute = urljoin(url, href)
        internal = norm_host(urlparse(absolute).netloc) == host
        links.append(Link(absolute, text, internal))
        if text and len(text) <= 45 and CTA_TEXT.search(text):
            ctas.append(text)
    for b in soup.find_all("button"):
        t = _text(b)
        if t and len(t) <= 45 and CTA_TEXT.search(t):
            ctas.append(t)

    images = [
        Image(src=i.get("src", ""), alt=i.get("alt"),
              has_dims=bool(i.get("width") and i.get("height")), lazy=i.get("loading") == "lazy")
        for i in soup.find_all("img")
    ]

    label_for = {l["for"] for l in soup.find_all("label", attrs={"for": True})}
    forms = []
    for f in soup.find_all("form"):
        fields = []
        for el in f.find_all(["input", "select", "textarea"]):
            ftype = el.name if el.name != "input" else (el.get("type") or "text").lower()
            if ftype in ("hidden", "submit", "button", "image", "reset"):
                continue
            fields.append(FormField(
                name=el.get("name") or el.get("id") or el.get("placeholder") or ftype,
                type=ftype,
                required=el.has_attr("required") or str(el.get("aria-required", "")).lower() == "true",
                labelled=_is_labelled(el, soup, label_for),
            ))
        btn = f.find("button") or f.find("input", attrs={"type": "submit"})
        submit = _text(btn) if btn and btn.name == "button" else (btn.get("value", "") if btn else "")
        forms.append(Form(fields=fields, submit_text=submit))

    # main readable text: drop scripts, chrome (header/nav/footer) and icon ligatures
    root = soup.find("main") or soup.body or soup
    work = BeautifulSoup(str(root), "html.parser")
    for el in work.find_all(["script", "style", "noscript", "svg", "template", "header", "nav", "footer"]):
        el.decompose()
    for el in work.find_all(class_=ICON_CLASS):
        el.decompose()
    for el in work.find_all(attrs={"aria-hidden": "true"}):
        el.decompose()

    headings = [[int(h.name[1]), _text(h)] for h in work.find_all(re.compile(r"^h[1-6]$")) if _text(h)]
    h1 = [t for lvl, t in headings if lvl == 1]
    main_text = "\n".join(
        line for line in (re.sub(r"\s+", " ", ln).strip() for ln in work.get_text("\n").splitlines()) if line
    )

    blocks = [_text(b).lower() for b in work.find_all(["p", "li", "blockquote"])]
    counts = Counter(b for b in blocks if len(b.split()) >= 8)
    duplicate_blocks = [b for b, n in counts.items() if n >= 2]

    visible_all = soup.get_text(" ")
    for m in PHONE.findall(visible_all):
        phones.append(re.sub(r"\D", "", m))
    emails.extend(e.lower() for e in EMAIL.findall(visible_all))

    return Page(
        url=url, status=status, has_markup=True, html_bytes=len(html.encode("utf-8", "ignore")),
        title=title, meta_description=meta_desc, canonical=canonical,
        lang=(soup.html.get("lang") if soup.html else None), viewport=viewport, og=og,
        h1=h1, headings=headings, main_text=main_text, word_count=len(main_text.split()),
        links=links, images=images, forms=forms, jsonld_types=_jsonld_types(soup),
        icon_leaks=list(dict.fromkeys(leaks)), anchors_missing=list(dict.fromkeys(anchors_missing)),
        duplicate_blocks=duplicate_blocks, phones=list(dict.fromkeys(phones)),
        emails=list(dict.fromkeys(emails)), ctas=ctas, scripts=len(soup.find_all("script")),
        published=published, headers={k: headers[k] for k in SECURITY_HEADERS if k in headers},
    )
