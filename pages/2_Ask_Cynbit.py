"""Ask Cynbit: the AI assistant that answers from the site's own pages."""
import json

import pandas as pd
import streamlit as st

from sitedoctor.assistant import LeadBook, SiteAssistant, cluster_questions
from sitedoctor.crawler import DATA_DIR
from sitedoctor.ui import current_site, site_banner

st.set_page_config(page_title="Ask Cynbit", page_icon="💬", layout="wide")
st.title("💬 Ask Cynbit")
st.markdown(
    "A demo of the assistant Cynbit could put on its own website. It **answers only from the site's pages**, shows which "
    "page it used, says *\"I could not find that\"* when the site does not say, and then offers to pass the question to the "
    "team. The questions it could not answer become a to-do list of content to write."
)

site = current_site()
site_banner(site)


@st.cache_resource
def build(key):
    return SiteAssistant(site)


assistant = build((site.base_url, site.fetched_at, site.kind))
ss = st.session_state
ss.setdefault("chat", [])
ss.setdefault("unanswered", [])
ss.setdefault("leads", LeadBook())
use_llm = st.sidebar.checkbox("Use an LLM to phrase answers (needs ANTHROPIC_API_KEY)", value=False)
st.sidebar.caption("Without a key the answer is the best matching sentences from the page.")

left, right = st.columns([3, 2])
with left:
    st.subheader("Try it as a visitor")
    st.caption("Ideas: *How much does BitElevate cost?*  |  *Who founded Cynbit?*  |  *What is the price of Cynbit Studio?*  |  "
               "*Do you have SOC 2?*")
    for m in ss["chat"]:
        with st.chat_message(m["role"]):
            st.write(m["text"])
            for s in m.get("sources", []):
                st.caption(f"Source: [{s['title']}]({s['url']})")
    q = st.chat_input("Ask about Cynbit's services, products, BitElevate, team or contact details")
    if q:
        ss["chat"].append({"role": "user", "text": q})
        a = assistant.answer(q, use_llm=use_llm)
        ss["chat"].append({"role": "assistant", "text": a.text, "sources": a.sources})
        if a.status == "not_found":
            ss["unanswered"].append(q)
            ss["pending_question"] = q
        else:
            ss.pop("pending_question", None)
        ss["last"] = a
        st.rerun()

    if "last" in ss:
        a = ss["last"]
        st.caption(f"Last answer: {a.status} | similarity {a.score:.2f} | key terms covered {a.coverage:.0%} | {a.mode}")

    if ss.get("pending_question"):
        with st.form("lead"):
            st.markdown(f"**Pass this to the team:** {ss['pending_question']}")
            name = st.text_input("Your name")
            email = st.text_input("Your email")
            if st.form_submit_button("Send to the team"):
                try:
                    ss["leads"].add(name, email, ss["pending_question"])
                    ss.pop("pending_question")
                    st.success("Captured. In production this would create a CRM entry and email the team.")
                except ValueError as exc:
                    st.error(str(exc))
        st.caption("Demo only: the details stay in this browser session and nothing is stored.")

with right:
    st.subheader("What the website is missing")
    st.caption("Questions the assistant could not answer, grouped by topic. This is the content to write next.")
    sample = json.loads((DATA_DIR / "assistant_eval.json").read_text(encoding="utf-8"))["visitor_questions_sample"]
    use_sample = st.checkbox("Add 20 example visitor questions (synthetic, for the demo)", value=False)
    qs = list(ss["unanswered"])
    if use_sample:
        qs += [s for s in sample if assistant.answer(s).status == "not_found"]
    groups = cluster_questions(qs)
    if groups:
        for g in groups:
            with st.expander(f"{g['topic']}  ({g['count']})"):
                for x in g["questions"]:
                    st.write("- " + x)
    else:
        st.write("Nothing yet. Ask something the site does not cover, such as pricing.")
    if ss["leads"].leads:
        st.subheader("Leads captured this session")
        st.dataframe(pd.DataFrame([l.__dict__ for l in ss["leads"].leads]), hide_index=True, width="stretch")
        st.download_button("Download leads (.csv)", ss["leads"].to_csv(), "leads.csv", "text/csv")
