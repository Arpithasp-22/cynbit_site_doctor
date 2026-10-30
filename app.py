"""Streamlit demo: streamlit run app.py"""
from __future__ import annotations

import io

import streamlit as st

from skillbridge.data import load_sample_resumes
from skillbridge.explain import explain
from skillbridge.extractor import extract_with_evidence
from skillbridge.matcher import RoleMatcher
from skillbridge.pathway import build_path

st.set_page_config(page_title="SkillBridge for Cynbit", page_icon="🌉", layout="wide")


@st.cache_resource
def get_matcher() -> RoleMatcher:
    return RoleMatcher()


def read_upload(file) -> str:
    if file.name.lower().endswith(".pdf"):
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file.read()))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file.read().decode("utf-8", errors="ignore")


st.title("SkillBridge")
st.caption(
    "Prototype for Cynbit Studio / BitElevate: match a resume to roles, explain the fit, "
    "and turn the gaps into a learning path. Roles and courses are illustrative, not Cynbit's real catalogue."
)

samples = {f"{r['id']} (expected: {r['expected_role']})": r["text"] for r in load_sample_resumes()}

with st.sidebar:
    st.header("Input")
    choice = st.selectbox("Load a synthetic sample", ["(none)"] + list(samples))
    upload = st.file_uploader("...or upload a resume (.txt or .pdf)", type=["txt", "pdf"])
    top_n = st.slider("Roles to show", 1, 5, 3)
    include_nice = st.checkbox("Include nice-to-have skills in the learning path", value=False)
    use_llm = st.checkbox("Use LLM explanation if ANTHROPIC_API_KEY is set", value=True)
    st.info("Do not paste real personal data into a shared deployment. Nothing is stored by this app.")

default_text = samples.get(choice, "")
if upload is not None:
    default_text = read_upload(upload)

resume = st.text_area("Resume text", value=default_text, height=220,
                      placeholder="Paste resume text here, or pick a sample in the sidebar")

if st.button("Analyse", type="primary") and resume.strip():
    matcher = get_matcher()
    evidence = extract_with_evidence(resume)
    matches = matcher.rank(resume)[:top_n]

    st.subheader("Detected skills")
    if evidence:
        st.write(", ".join(f"`{s}`" for s in sorted(evidence)))
        with st.expander("Why were these detected? (evidence)"):
            for skill, snippet in sorted(evidence.items()):
                st.markdown(f"**{skill}**: ...{snippet}...")
    else:
        st.warning("No known skills detected. Try adding a skills section.")

    st.subheader("Best-fit roles")
    for rank, m in enumerate(matches, 1):
        path = build_path(m, include_nice_to_have=include_nice)
        with st.expander(f"#{rank}  {m.role.title}  ·  fit {m.score:.0%}", expanded=rank == 1):
            c1, c2, c3 = st.columns(3)
            c1.metric("Overall fit", f"{m.score:.0%}")
            c2.metric("Skill coverage", f"{m.skill_score:.0%}")
            c3.metric("Text similarity", f"{m.text_score:.0%}")
            st.progress(min(1.0, m.score))

            left, right = st.columns(2)
            left.markdown("**Matched required skills**")
            left.write(", ".join(sorted(m.matched_required)) or "none")
            right.markdown("**Missing required skills**")
            right.write(", ".join(m.missing_required) or "none")

            if path.steps:
                st.markdown(f"**Learning path** ({path.total_hours} hours)")
                st.table(
                    [{"Course": s.course.title, "Track": s.course.track,
                      "Hours": s.course.hours, "Closes": ", ".join(s.closes)} for s in path.steps]
                )
            if path.uncovered:
                st.caption("Not covered by any catalogue course: " + ", ".join(path.uncovered))

            text, source = explain(m, path, use_llm=use_llm)
            st.markdown(f"**Explanation** _(source: {source})_")
            st.write(text)
elif not resume.strip():
    st.info("Add a resume to begin.")
