import pytest

from proofkit.casestudy import (Evidence, Metric, draft, evidence_request, load_sample_evidence,
                                numbers_preserved, polish)
from proofkit.claims import audit_claim, audit_claims, audit_page, load_site_claims, summarise


# ---------- claim auditor ----------

def test_bare_percentage_is_flagged_for_all_three_gaps():
    f = audit_claim("t", "40% increase in organic leads")
    assert {"no time period", "no baseline", "no source"} <= set(f.issues)
    assert f.severity == "high"


def test_well_supported_claim_passes():
    f = audit_claim("t", "Organic leads grew 40% from 100 to 140 per month in Jan-Jun 2025 (source: Google Analytics export)")
    assert f.issues == [] and f.severity == "ok"


def test_absolute_claim_is_high_severity():
    f = audit_claim("t", "100% success")
    assert f.severity == "high" and any("absolute" in i for i in f.issues)


def test_vague_superlative_flagged_without_numeric_gaps():
    f = audit_claim("t", "A revolutionary approach to architecture")
    assert f.issues == ["vague superlative, not measurable"] and f.severity == "low"


def test_always_on_claim_asks_for_coverage_detail_not_baseline_or_period():
    f = audit_claim("t", "24/7 support")
    assert f.issues == ["no coverage detail"] and f.severity == "low"
    detailed = audit_claim("t", "24/7 support by phone and email with a 2-hour response target")
    assert detailed.issues == []


def test_structured_context_can_satisfy_checks():
    f = audit_claim("t", "99.9% uptime", extra_context="source: StatusCake report period: 2025 baseline: from 99.5%")
    assert f.severity != "high"


def test_text_without_claims_yields_nothing():
    assert audit_page("We build software. Contact us in Jaipur.") == []


def test_audit_page_finds_claims_per_sentence_and_sorts_by_severity():
    text = "We are premier. Uptime rose from 99% to 99.9% in 2025 (source: audit).\nTrusted by 1000+ clients."
    findings = audit_page(text)
    assert len(findings) == 3
    sev = [f.severity for f in findings]
    assert sev == sorted(sev, key=lambda s: {"high": 0, "medium": 1, "low": 2, "ok": 3}[s])


def test_site_claims_file_audits_and_none_are_fully_supported():
    findings = audit_claims(load_site_claims())
    counts = summarise(findings)
    assert counts["total"] == len(load_site_claims())
    assert counts["ok"] == 0  # the page gives no sources, which is the finding


# ---------- case-study drafter ----------

def test_metric_gates_require_baseline_period_source_and_verification():
    m = Metric("Uptime", 99.9)
    assert not m.publishable() and len(m.missing()) == 4
    ok = Metric("Leads", 140, baseline=100, timeframe="H1 2025", source="GA export", verified=True)
    assert ok.publishable() and ok.change_pct() == pytest.approx(40.0)


def test_change_pct_handles_text_and_zero_baseline():
    assert Metric("x", "100%", baseline=None).change_pct() is None
    assert Metric("x", 5, baseline=0).change_pct() is None


def test_draft_publishes_only_verified_metrics():
    ev = load_sample_evidence()[0]
    d = draft(ev)
    assert len(d.published) == 2 and len(d.held_back) == 2
    assert "100 to 140 leads/month (+40%)" in d.markdown
    assert "Uptime" not in d.markdown and "100%" not in d.markdown
    assert "requires client approval" in d.markdown


def test_unverified_metrics_are_labelled_when_included():
    d = draft(load_sample_evidence()[0], include_unverified=True)
    assert d.markdown.count("[UNVERIFIED, do not publish]") == 2


def test_quote_is_omitted_without_consent():
    ev = load_sample_evidence()[0]
    ev.quote["consent"] = False
    assert "In the client's words" not in draft(ev).markdown
    assert "written permission" in evidence_request(ev)


def test_no_metrics_does_not_invent_results():
    d = draft(Evidence(client="Acme", problem="p", solution="s"))
    assert "No verified metrics yet" in d.markdown


def test_evidence_request_lists_exact_gaps():
    req = evidence_request(load_sample_evidence()[0])
    assert "Uptime" in req and "baseline" in req and "source" in req
    assert "Organic leads" not in req  # fully evidenced metrics are not requested again


def test_number_guardrail():
    assert numbers_preserved("Leads rose 100 to 140 (+40%)", "Leads climbed from 100 to 140, up 40%")
    assert not numbers_preserved("Leads rose 100 to 140", "Leads rose 100 to 150")
    assert not numbers_preserved("Leads rose 100 to 140", "Leads rose 100 to 140 and 3x ROI")


def test_polish_without_key_returns_input(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    text, source = polish("# x\n40%")
    assert text == "# x\n40%" and source.startswith("unchanged")
