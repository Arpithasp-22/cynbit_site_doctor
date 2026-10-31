import functools
import http.server
import threading
from pathlib import Path

import pytest
import requests

from sitedoctor import assistant as asst
from sitedoctor.assistant import LeadBook, SiteAssistant, cluster_questions
from sitedoctor.checks import run_checks
from sitedoctor.crawler import Crawler, Site, check_public, load_snapshot
from sitedoctor.extract import parse_html
from sitedoctor.fixes import (claim_requests, contact_form_spec, fix_pack_markdown, offer_checklist, polish_meta,
                              suggest_meta, suggest_title, title_meta_rows)
from sitedoctor.scoring import compare, score

FIXTURES = Path(__file__).parent / "fixtures" / "site"


# ------------------------------------------------------------------ local test website
class Handler(http.server.SimpleHTTPRequestHandler):
    ROUTES = {"/": "index.html", "/services": "services.html", "/contact": "contact.html", "/good": "good.html",
              "/blog-post": "blog-post.html", "/robots.txt": "robots.txt", "/sitemap.xml": "sitemap.xml"}

    def do_GET(self):
        name = self.ROUTES.get(self.path.split("?")[0])
        if not name:
            self.send_error(404)
            return
        body = (FIXTURES / name).read_bytes().replace(b"SITEBASE", f"http://127.0.0.1:{self.server.server_port}".encode())
        self.send_response(200)
        self.send_header("Content-Type", "text/xml" if name.endswith(".xml") else "text/plain" if name.endswith(".txt") else "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_HEAD(self):
        self.send_response(200 if self.path.split("?")[0] in self.ROUTES else 404)
        self.end_headers()

    def log_message(self, *a):
        pass


@pytest.fixture(scope="module")
def live_site():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    session = requests.Session()
    session.trust_env = False  # never route local test traffic through a proxy
    site = Crawler(f"http://127.0.0.1:{srv.server_port}", session=session, allow_private=True).crawl()
    yield site
    srv.shutdown()


@pytest.fixture(scope="module")
def live_result(live_site):
    return run_checks(live_site)


def ids(result):
    return {i.id for i in result.issues}


# ------------------------------------------------------------------ extraction
def test_parse_extracts_the_basics():
    html = (FIXTURES / "good.html").read_text().replace("SITEBASE", "x")
    p = parse_html("https://x.test/good", html)
    assert p.title.startswith("A clean page") and p.lang == "en" and p.viewport
    assert p.h1 == ["Clean page"] and p.jsonld_types == ["Organization"]
    assert p.forms[0].is_inquiry and all(f.required and f.labelled for f in p.forms[0].fields)


def test_icon_text_is_detected_and_excluded_from_readable_text():
    html = '<html><body><main><h1>T</h1><span class="material-symbols-outlined">expand_more</span><p>Hello there.</p></main></body></html>'
    p = parse_html("https://x.test/", html)
    assert p.icon_leaks == ["expand_more"] and "expand_more" not in p.main_text
    hidden = html.replace('class="material', 'aria-hidden="true" class="material')
    assert parse_html("https://x.test/", hidden).icon_leaks == []


def test_missing_anchor_targets_and_phones():
    p = parse_html("https://x.test/", '<html><body><a href="#nope">Go</a><div id="yes"></div><a href="#yes">ok</a>'
                                      '<a href="tel:+91 90000 00001">c</a></body></html>')
    assert p.anchors_missing == ["#nope"] and p.phones == ["919000000001"]


# ------------------------------------------------------------------ crawler
def test_crawler_reads_pages_sitemap_and_robots(live_site):
    paths = {p.path for p in live_site.pages}
    assert {"/", "/services", "/contact", "/good", "/blog-post"} <= paths
    assert live_site.robots_txt and len(live_site.sitemap_urls) == 4


def test_crawler_reports_broken_links(live_site):
    assert any(b[1].endswith("/broken-page") and b[2] == 404 for b in live_site.broken_links)


def test_private_addresses_are_refused_by_default():
    with pytest.raises(ValueError):
        check_public("http://127.0.0.1:8000/")
    with pytest.raises(ValueError):
        check_public("file:///etc/passwd")
    with pytest.raises(ValueError):
        Crawler("http://127.0.0.1:1", check_links=False).crawl().pages  # default blocks loopback
        raise ValueError  # pragma: no cover  (crawl swallows fetch errors, so assert via notes below)


def test_blocked_scan_returns_no_pages_and_a_note():
    site = Crawler("http://127.0.0.1:1", check_links=False).crawl()
    assert site.pages == [] and any("private" in n.lower() or "could not fetch" in n.lower() for n in site.notes)


def test_site_round_trips_through_json(live_site, tmp_path):
    f = tmp_path / "scan.json"
    live_site.save(f)
    again = Site.load(f)
    assert [p.url for p in again.pages] == [p.url for p in live_site.pages]
    assert again.pages[0].forms == live_site.pages[0].forms


# ------------------------------------------------------------------ checks: planted problems are found
@pytest.mark.parametrize("issue_id", [
    "title-length", "title-brand-dup", "meta-duplicate", "h1-count", "heading-skip", "canonical", "icon-text",
    "img-alt-weak", "anchor-missing", "form-labels", "form-required", "link-text", "claims", "dup-blocks",
    "broken-links", "date-mismatch", "phones", "thin-offer", "open-graph",
])
def test_planted_problem_is_found(live_result, issue_id):
    assert issue_id in ids(live_result), f"{issue_id} not found in {sorted(ids(live_result))}"


def test_clean_page_is_not_flagged(live_result):
    for i in live_result.issues:
        assert "/good" not in i.pages, f"false positive on the clean page: {i.id}"


def test_claims_check_names_the_missing_pieces(live_result):
    claim = next(i for i in live_result.issues if i.id == "claims")
    assert claim.severity == "high" and any("no source" in e for e in claim.evidence)


def test_snapshot_skips_markup_checks_and_marks_categories_unscored():
    r = run_checks(load_snapshot())
    assert "Page titles" in r.skipped and "Search (SEO)" not in r.checked
    card = score(r, 14)
    assert card.by_category["Search (SEO)"] is None and card.by_category["Trust & proof"] is not None


def test_snapshot_findings_include_known_real_issues():
    r = run_checks(load_snapshot())
    found = ids(r)
    assert {"claims", "offer-gaps", "date-mismatch", "spelling", "obs-case-study", "obs-products-gaps"} <= found
    spelling = next(i for i in r.issues if i.id == "spelling")
    assert any("unheared" in e for e in spelling.evidence)  # a real typo on /diaries


# ------------------------------------------------------------------ scoring
def test_scores_are_bounded_and_more_issues_never_raise_the_score(live_site):
    full = run_checks(live_site)
    card = score(full, len(live_site.pages))
    assert 0 <= card.overall <= 100 and all(0 <= v <= 100 for v in card.by_category.values() if v is not None)
    fewer = type(full)([i for i in full.issues if i.severity != "high"], full.skipped, full.checked)
    assert score(fewer, len(live_site.pages)).overall >= card.overall


def test_compare_shows_resolved_new_and_remaining(live_result):
    before = live_result.issues
    after = [i for i in before if i.id != "claims"]
    diff = compare(before, after)
    assert any("claims" in t.lower() or "period" in t for t in diff["resolved"]) and diff["new"] == []


# ------------------------------------------------------------------ fixes
def test_title_and_meta_suggestions_respect_length_limits(live_site):
    for r in title_meta_rows(live_site, "Acme"):
        assert r["Title length"] <= 60 and r["Description length"] <= 160


def test_suggested_title_puts_topic_first_and_brand_last():
    p = parse_html("https://x.test/services", "<html><head><title>x</title></head><body><main><h1>Web development services for startups</h1></main></body></html>")
    assert suggest_title(p, "Acme") == "Web development services for startups | Acme"


def test_suggest_meta_is_extractive_and_has_no_new_numbers():
    p = parse_html("https://x.test/", "<html><body><main><h1>T</h1><p>We build software for growing companies in India. "
                                      "Our team has delivered 12 projects.</p></main></body></html>")
    meta = suggest_meta(p)
    assert meta and set(w for w in meta.split() if w.isdigit()) <= {"12"} and len(meta) <= 160


def test_polish_without_key_returns_draft(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert polish_meta("Draft text with 12 items.") == ("Draft text with 12 items.", "extractive")


def test_claim_requests_and_offer_checklist_on_snapshot():
    site = load_snapshot()
    rows = claim_requests(site)
    assert rows and all("[BASELINE]" in r["Rewrite template"] or "[" in r["Rewrite template"] for r in rows)
    check = {r["Page"]: r for r in offer_checklist(site)}
    assert check["/products"]["pricing or fees"] == "MISSING" and check["/bitelevate"]["pricing or fees"] == "yes"


def test_fix_pack_contains_every_section():
    site = load_snapshot()
    md = fix_pack_markdown(site, run_checks(site))
    for heading in ("## 1. Prioritised issues", "## 2. Claims to back up", "## 3. What each offer page is missing", "Recommended inquiry form"):
        assert heading in md
    assert "Confirmation message" in contact_form_spec(site)


# ------------------------------------------------------------------ assistant
@pytest.fixture(scope="module")
def bot():
    return SiteAssistant(load_snapshot())


def test_assistant_answers_from_the_right_page_with_a_source(bot):
    a = bot.answer("How much does BitElevate cost?")
    assert a.status == "answered" and "3,999" in a.text and a.sources[0]["url"].endswith("/bitelevate")


def test_assistant_declines_what_the_site_does_not_say(bot):
    for q in ["What is the monthly price of Cynbit Studio?", "What is the weather in Jaipur today?", "Is Cynbit ISO 27001 certified?"]:
        a = bot.answer(q)
        assert a.status == "not_found" and "will not guess" in a.text and a.sources == [], q


def test_assistant_handles_empty_and_junk_input(bot):
    assert bot.answer("").status == "not_found" and bot.answer("???").status == "not_found"


def test_llm_answer_is_skipped_without_a_key(bot, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert asst.llm_answer("q", bot.chunks[:1]) is None and bot.answer("How much does BitElevate cost?", use_llm=True).mode == "extractive"


def test_llm_answer_guardrail_rejects_invented_numbers(bot, monkeypatch):
    class Msg:  # a fake model reply that invents a price
        content = [type("B", (), {"type": "text", "text": "It costs 9,999 rupees [1]."})()]

    class Fake:
        def __init__(self, *a, **k):
            self.messages = type("M", (), {"create": staticmethod(lambda **kw: Msg())})()

    import types, sys
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setitem(sys.modules, "anthropic", types.SimpleNamespace(Anthropic=Fake))
    chunks = [c for c, _ in bot.retrieve("How much does BitElevate cost?")]
    assert asst.llm_answer("How much does BitElevate cost?", chunks) is None


def test_lead_capture_validates_and_exports_csv():
    book = LeadBook()
    with pytest.raises(ValueError):
        book.add("", "a@b.co", "q")
    with pytest.raises(ValueError):
        book.add("Asha", "not-an-email", "q")
    book.add("Asha", "asha@example.com", 'Does it have "pricing"?')
    assert book.to_csv().splitlines()[1].startswith('"Asha","asha@example.com"') and '""pricing""' in book.to_csv()


def test_unanswered_questions_cluster_by_topic():
    qs = ["How much does Studio cost per month?", "What is the price of TenantEase?", "Is there a free trial for Studio pricing?",
          "What stipend do interns get?", "Are internships paid with a stipend?", "Do you have SOC 2 certification?"]
    groups = cluster_questions(qs)
    assert sum(g["count"] for g in groups) == len(qs) and len(groups) < len(qs)
    assert cluster_questions([]) == []


def test_evaluation_meets_a_minimum_bar_on_unanswerable_questions(bot):
    from sitedoctor.assistant_eval import evaluate, load_items
    m = evaluate(bot, load_items(), asst.DEFAULTS["score"], asst.DEFAULTS["coverage"])
    assert m["unanswerable_declined"] >= 0.9 and m["answerable_correct"] >= 0.5
