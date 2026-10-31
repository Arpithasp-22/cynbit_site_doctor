"""Case Study Drafter page: only evidenced metrics get published."""
import json
from dataclasses import asdict

import streamlit as st

from proofkit.casestudy import Evidence, draft, evidence_request, load_sample_evidence, polish

st.set_page_config(page_title="Case Study Drafter", page_icon="📝", layout="wide")
st.title("Case Study Drafter")
st.caption(
    "Turns structured client evidence into a case-study draft. A metric is published only if it has a "
    "baseline, a time period, a source and client confirmation. Everything else is held back and "
    "listed in a request for the client. The sample client below is fictional."
)

sample = load_sample_evidence()[0]
default_json = json.dumps(
    {k: v for k, v in asdict(sample).items()}, indent=2
)

left, right = st.columns([1, 1])
with left:
    st.subheader("Evidence (editable JSON)")
    raw = st.text_area("Client evidence", value=default_json, height=520, label_visibility="collapsed")
    include_unverified = st.checkbox("Show unverified metrics in the draft (clearly labelled)", value=False)
    use_llm = st.checkbox("Polish wording with an LLM if ANTHROPIC_API_KEY is set", value=False)

try:
    ev = Evidence.from_dict(json.loads(raw))
except Exception as exc:  # invalid JSON or missing fields
    st.error(f"Could not read the evidence: {exc}")
    st.stop()

result = draft(ev, include_unverified=include_unverified)
markdown = result.markdown
source = "template"
if use_llm:
    markdown, source = polish(markdown)

with right:
    st.subheader("Draft")
    c1, c2 = st.columns(2)
    c1.metric("Metrics ready to publish", len(result.published))
    c2.metric("Held back", len(result.held_back))
    st.markdown(markdown)
    st.caption(f"Wording source: {source}")
    st.download_button("Download draft (.md)", markdown, "case_study_draft.md", "text/markdown")

st.divider()
st.subheader("What to ask the client")
st.markdown(evidence_request(ev))
