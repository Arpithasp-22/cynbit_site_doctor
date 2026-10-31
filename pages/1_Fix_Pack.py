"""Fix Pack: the fixes themselves, ready to copy."""
import pandas as pd
import streamlit as st

from sitedoctor.fixes import (claim_requests, contact_form_spec, fix_pack_markdown, offer_checklist, polish_meta,
                              title_meta_rows)
from sitedoctor.ui import analysis, current_site, site_banner

st.set_page_config(page_title="Fix Pack", page_icon="🧰", layout="wide")
st.title("🧰 Fix Pack")
st.caption("Drafts for the web team. A person should review each one before it goes live.")

site = current_site()
result, _ = analysis(site)
site_banner(site)

t1, t2, t3, t4 = st.tabs(["Back up the claims", "What offer pages are missing", "Titles and descriptions", "Contact form"])

with t1:
    st.markdown("Every number below has no period, baseline or source next to it. For each one, collect the facts "
                "and use the rewrite template. **A flag does not mean the claim is false.**")
    rows = claim_requests(site)
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    else:
        st.success("No unsupported claims found.")

with t2:
    st.markdown("What a buyer looks for before they contact anyone. `MISSING` means the page text has no sign of it "
                "(a keyword check, so confirm by eye).")
    rows = offer_checklist(site)
    if rows:
        df = pd.DataFrame(rows)
        st.dataframe(df.style.map(lambda v: "background-color:#fde2e2" if v == "MISSING" else "", subset=df.columns[1:]),
                     width="stretch", hide_index=True)

with t3:
    if not any(p.has_markup for p in site.pages):
        st.info("Titles and descriptions come from the page markup. Run a live scan to generate drafts for every page.")
    else:
        brand = st.text_input("Brand name", "Cynbit")
        rows = title_meta_rows(site, brand)
        if st.checkbox("Polish descriptions with an LLM (needs ANTHROPIC_API_KEY; rejected if it changes any number)"):
            for r in rows:
                r["Suggested description"], _src = polish_meta(r["Suggested description"])
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)

with t4:
    st.markdown(contact_form_spec(site))

st.divider()
st.download_button("Download everything as one file (.md)", fix_pack_markdown(site, result), "cynbit_fix_pack.md", "text/markdown")
