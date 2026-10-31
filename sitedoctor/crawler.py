"""Polite, safe crawler: robots.txt, sitemap, same-site links, size caps, no private addresses."""
from __future__ import annotations

import ipaddress
import json
import re
import socket
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib import robotparser
from urllib.parse import urljoin, urlparse

import requests

from .extract import Page, norm_host, parse_html

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USER_AGENT = "SiteDoctor/0.1 (assessment prototype; read-only)"
SKIP_EXT = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".pdf", ".zip", ".css", ".js",
            ".json", ".xml", ".txt", ".mp4", ".woff", ".woff2", ".map")


@dataclass
class Site:
    base_url: str
    kind: str = "live"  # "live" (real HTML) or "snapshot-text" (text only, markup checks skipped)
    fetched_at: str = ""
    pages: list[Page] = field(default_factory=list)
    robots_txt: str | None = None
    sitemap_urls: list[str] = field(default_factory=list)
    broken_links: list[list] = field(default_factory=list)  # [found_on, url, status]
    notes: list[str] = field(default_factory=list)
    observations: list[dict] = field(default_factory=list)  # findings from a human read (snapshot only)

    def page(self, path: str) -> Page | None:
        return next((p for p in self.pages if p.path == path), None)

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["pages"] = [p.to_dict() for p in self.pages]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Site":
        d = dict(d)
        d["pages"] = [Page.from_dict(p) for p in d.get("pages", [])]
        return cls(**d)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "Site":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def load_snapshot() -> Site:
    """Offline demo data: a text-only, paraphrased snapshot of cynbit.in taken on 30 Oct 2026."""
    raw = json.loads((DATA_DIR / "snapshot" / "cynbit_pages.json").read_text(encoding="utf-8"))
    pages = []
    for p in raw["pages"]:
        text = p["text"].strip()
        pages.append(Page(
            url=p["url"], has_markup=False, title=p.get("title"), h1=p.get("h1", []),
            headings=[[2, h] for h in p.get("headings", [])], main_text=text, word_count=len(text.split()),
            published=p.get("published"),
        ))
    return Site(base_url=raw["base_url"], kind="snapshot-text", fetched_at=raw["captured"],
                pages=pages, notes=[raw["_note"]], observations=raw.get("observations", []))


def normalise_url(url: str) -> str:
    u = urlparse(url)
    path = u.path.rstrip("/") or ""
    return f"{u.scheme}://{u.netloc.lower()}{path}"


def check_public(url: str) -> None:
    """Refuse non-http(s) URLs and hosts that resolve to private or local addresses (SSRF guard)."""
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise ValueError("Only http(s) URLs are allowed.")
    try:
        infos = socket.getaddrinfo(u.hostname, None)
    except socket.gaierror as exc:
        raise ValueError(f"Could not resolve {u.hostname}: {exc}") from exc
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise ValueError("Refusing to scan a private or local address.")


class Crawler:
    def __init__(self, base_url: str, max_pages: int = 25, timeout: float = 10, session=None,
                 allow_private: bool = False, max_bytes: int = 2_000_000, check_links: bool = True,
                 max_link_checks: int = 60, delay: float = 0.0):
        if "://" not in base_url:
            base_url = "https://" + base_url
        self.base = base_url.rstrip("/")
        self.host = norm_host(urlparse(self.base).netloc)
        self.max_pages, self.timeout, self.max_bytes = max_pages, timeout, max_bytes
        self.allow_private, self.check_links = allow_private, check_links
        self.max_link_checks, self.delay = max_link_checks, delay
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.robots = robotparser.RobotFileParser()
        self.robots_text: str | None = None

    # ---- network ----
    def _get(self, url: str):
        if not self.allow_private:
            check_public(url)
        resp = self.session.get(url, timeout=self.timeout, stream=True, allow_redirects=True)
        if not self.allow_private:
            check_public(resp.url)  # a redirect must not lead to a private address
        chunks, size = [], 0
        for chunk in resp.iter_content(8192):
            chunks.append(chunk)
            size += len(chunk)
            if size >= self.max_bytes:
                break
        resp.close()
        body = b"".join(chunks).decode(resp.encoding or "utf-8", errors="replace")
        return resp, body

    def _internal(self, url: str) -> bool:
        return norm_host(urlparse(url).netloc) == self.host

    def _allowed(self, url: str) -> bool:
        return self.robots_text is None or self.robots.can_fetch(USER_AGENT, url)

    # ---- discovery ----
    def _read_robots(self) -> list[str]:
        sitemaps: list[str] = []
        try:
            resp, body = self._get(self.base + "/robots.txt")
            if resp.status_code == 200 and "html" not in resp.headers.get("content-type", "").lower():
                self.robots_text = body
                self.robots.parse(body.splitlines())
                sitemaps = re.findall(r"(?im)^\s*sitemap:\s*(\S+)", body)
        except (requests.RequestException, ValueError):
            pass
        return sitemaps

    def _read_sitemaps(self, urls: list[str]) -> list[str]:
        found: list[str] = []
        queue = list(urls) or [self.base + "/sitemap.xml"]
        seen = 0
        while queue and seen < 6:
            sm = queue.pop(0)
            seen += 1
            try:
                resp, body = self._get(sm)
            except (requests.RequestException, ValueError):
                continue
            if resp.status_code != 200:
                continue
            locs = re.findall(r"<loc>\s*(.*?)\s*</loc>", body, flags=re.I | re.S)
            if "<sitemapindex" in body.lower():
                queue.extend(locs[:5])
            else:
                found.extend(locs)
        return found

    # ---- main ----
    def crawl(self) -> Site:
        site = Site(base_url=self.base, kind="live", fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
        sitemap_hints = self._read_robots()
        site.robots_txt = self.robots_text
        site.sitemap_urls = [u for u in self._read_sitemaps(sitemap_hints) if self._internal(u)]

        queue = [self.base] + site.sitemap_urls
        seen: set[str] = set()
        discovered: dict[str, str] = {}  # internal link -> first page it was found on
        while queue and len(site.pages) < self.max_pages:
            url = queue.pop(0)
            key = normalise_url(url)
            if key in seen or key.lower().endswith(SKIP_EXT) or not self._internal(url):
                continue
            seen.add(key)
            if not self._allowed(url):
                site.notes.append(f"Skipped by robots.txt: {url}")
                continue
            try:
                resp, body = self._get(url)
            except (requests.RequestException, ValueError) as exc:
                site.notes.append(f"Could not fetch {url}: {exc}")
                continue
            ctype = resp.headers.get("content-type", "").lower()
            if resp.status_code >= 400:
                site.broken_links.append([url, url, resp.status_code])
                continue
            if "html" not in ctype:
                continue
            page = parse_html(resp.url, body, resp.status_code, dict(resp.headers))
            site.pages.append(page)
            for link in page.links:
                if link.internal:
                    k = normalise_url(link.href)
                    discovered.setdefault(k, page.url)
                    if k not in seen:
                        queue.append(link.href)
            if self.delay:
                time.sleep(self.delay)

        if self.check_links:
            crawled = {normalise_url(p.url) for p in site.pages}
            to_check = [(src, u) for u, src in discovered.items()
                        if u not in crawled and not u.lower().endswith(SKIP_EXT)][: self.max_link_checks]
            for src, u in to_check:
                status = self._head(u)
                if status >= 400 or status == 0:
                    site.broken_links.append([src, u, status])
        site.broken_links = [b for i, b in enumerate(site.broken_links) if b not in site.broken_links[:i]]
        if len(site.pages) >= self.max_pages and queue:
            site.notes.append(f"Stopped at {self.max_pages} pages; the site has more.")
        return site

    def _head(self, url: str) -> int:
        try:
            if not self.allow_private:
                check_public(url)
            r = self.session.head(url, timeout=self.timeout, allow_redirects=True)
            if r.status_code in (405, 403, 501):
                r = self.session.get(url, timeout=self.timeout, stream=True, allow_redirects=True)
                r.close()
            return r.status_code
        except (requests.RequestException, ValueError):
            return 0
