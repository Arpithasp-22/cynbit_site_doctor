"""Cynbit Site Doctor. Run: streamlit run app.py"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sitedoctor.checks import CATEGORIES, EFFORT_LABEL
from sitedoctor.crawler import Crawler
from sitedoctor.fixes import fix_pack_markdown
from sitedoctor.ui import analysis, current_site, site_banner

st.set_page_config(page_title="Cynbit Site Doctor", page_icon="🩺", layout="wide")

st.title("🩺 Cynbit Site Doctor")
st.markdown(
    "**A website checkup for cynbit.in that tells the team exactly what to fix, in what order, and gives them the "
    "fixes ready to use.**"
)

with st.sidebar:
    st.header("Source")
    mode = st.radio("What should I check?", ["Saved snapshot of cynbit.in", "Scan a live website"])
    if mode == "Scan a live website":
        url = st.text_input("Website address", "https://www.cynbit.in")
        pages = st.slider("Maximum pages to read", 5, 40, 20)
        if st.button("Scan now", type="primary"):
            with st.spinner("Reading the site..."):
                try:
                    st.session_state["site"] = Crawler(url, max_pages=pages).crawl()
                except Exception as exc:
                    st.error(f"Could not scan that address: {exc}")
    else:
        st.session_state.pop("site", None)
    st.caption("The scanner reads pages like a browser does, follows only same-site links, respects robots.txt and "
               "never visits private addresses.")

c1, c2, c3 = st.columns(3)
c1.markdown("### 1. Scan\nRead every page the way a visitor's browser and Google do.")
c2.markdown("### 2. Diagnose\n23 checks across trust, content, conversion, search, accessibility and hygiene. "
            "Every finding says **what, why, where and how to fix it**.")
c3.markdown("### 3. Fix\nReady-to-use fixes (claim rewrites, page checklists, contact form spec) and "
            "**Ask Cynbit**, an AI assistant that answers visitors from the site's own pages and shows what is missing.")

site = current_site()
result, card = analysis(site)
site_banner(site)

st.subheader("Scorecard")
cols = st.columns(len(CATEGORIES) + 1)
cols[0].metric("Overall", f"{card.overall}/100" if card.overall is not None else "n/a")
for col, cat in zip(cols[1:], CATEGORIES):
    v = card.by_category[cat]
    col.metric(cat, f"{v}" if v is not None else "needs live scan")
st.caption("A heuristic health score, not a Google ranking. Each issue subtracts points by severity and by how many "
           "pages it affects; categories that cannot be checked from the snapshot are left blank (not scored 100), and Overall averages only the categories that were checked.")
if result.skipped:
    with st.expander(f"{len(result.skipped)} checks need the real page markup (run a live scan)"):
        st.write(", ".join(result.skipped))

wins = card.quick_wins[:5]
if wins:
    st.subheader("Start here: quick wins")
    st.caption("High or medium impact, under an hour each.")
    for i in wins:
        st.markdown(f"- **{i.title}**: {i.fix}")

st.subheader(f"All findings ({card.counts['total']})")
f1, f2, f3 = st.columns([2, 2, 1])
sev = f1.multiselect("Priority", ["high", "medium", "low"], default=["high", "medium", "low"])
cat = f2.multiselect("Area", CATEGORIES, default=CATEGORIES)
only_quick = f3.checkbox("Quick wins only")
shown = [i for i in result.issues if i.severity in sev and i.category in cat and (i.quick_win or not only_quick)]

df = pd.DataFrame([{
    "Priority": i.severity, "Area": i.category, "Finding": i.title, "Time to fix": EFFORT_LABEL[i.effort],
    "Pages": len(i.pages), "How we know": {"html": "checked on HTML", "text": "checked on text",
                                           "observed": "found by reading"}[i.source],
    "Confidence": i.confidence} for i in shown])
st.dataframe(df, width="stretch", hide_index=True)

for i in shown:
    with st.expander(f"[{i.severity.upper()}] {i.title}"):
        st.markdown(f"**Why it matters.** {i.why}")
        st.markdown(f"**How to fix it.** {i.fix}")
        if i.pages:
            st.markdown("**Where:** " + ", ".join(f"`{p}`" for p in i.pages[:10]))
        if i.evidence:
            st.markdown("**Evidence:**\n" + "\n".join(f"- {e}" for e in i.evidence[:6]))
        st.caption(f"{i.category} | time to fix: {EFFORT_LABEL[i.effort]} | confidence: {i.confidence} | "
                   f"{'found by a human reading the pages' if i.source == 'observed' else 'found by code'}")

st.divider()
d1, d2 = st.columns(2)
d1.download_button("Download the Fix Pack (.md)", fix_pack_markdown(site, result), "cynbit_fix_pack.md", "text/markdown")
d2.download_button("Download findings (.csv)", df.to_csv(index=False), "cynbit_findings.csv", "text/csv")
st.caption("Next: open **Fix Pack** and **Ask Cynbit** in the sidebar.")
