"""How it works: the plain-language explanation, rendered from docs/explainer.md."""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="How it works", page_icon="📖", layout="wide")
st.markdown((Path(__file__).resolve().parent.parent / "docs" / "explainer.md").read_text(encoding="utf-8"))
