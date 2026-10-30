"""Claim Audit page: flag website claims that cannot be checked from the page itself."""
import pandas as pd
import streamlit as st

from proofkit.claims import audit_claims, audit_page, load_site_claims, summarise

st.set_page_config(page_title="Claim Audit", page_icon="🔎", layout="wide")
st.title("Claim Audit")
st.caption(
    "Flags claims that give a reader no way to check them: no time period, no baseline, no source. "
    "A flag does NOT mean the claim is false. It means the page does not back it up."
)

mode = st.radio("What to audit", ["Claims seen on cynbit.in (text read, 30 Oct 2026)", "Paste any page text"],
                horizontal=True)

if mode.startswith("Claims"):
    findings = audit_claims(load_site_claims())
    st.caption("Short paraphrases from the homepage and Our Story page. Product and client names come from the site.")
else:
    text = st.text_area("Page text", height=200, placeholder="Paste copy from any web page here")
    findings = audit_page(text) if text.strip() else []
    if not text.strip():
        st.info("Paste some copy to audit.")

if findings:
    s = summarise(findings)
    c = st.columns(4)
    c[0].metric("Claims checked", s["total"])
    c[1].metric("High priority", s["high"])
    c[2].metric("Medium", s["medium"])
    c[3].metric("Low", s["low"])

    rows = [{"Priority": f.severity, "Claim": f.text, "Client": f.client or "",
             "Problems": "; ".join(f.issues) or "none", "How to fix": f.suggestion} for f in findings]
    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)
    st.download_button("Download as CSV", df.to_csv(index=False), "claim_audit.csv", "text/csv")

    st.markdown(
        "**Example of a claim that would pass:** *Organic leads grew 40% from 100 to 140 per month "
        "in Jan-Jun 2025 (source: Google Analytics export).* It names the period, the starting point and the source."
    )
