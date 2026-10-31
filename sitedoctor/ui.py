"""Small helpers shared by the Streamlit pages."""
from __future__ import annotations

import streamlit as st

from .checks import Result, run_checks
from .crawler import Site, load_snapshot
from .scoring import Scorecard, score


@st.cache_resource
def snapshot_site() -> Site:
    return load_snapshot()


def current_site() -> Site:
    return st.session_state.get("site") or snapshot_site()


def analysis(site: Site) -> tuple[Result, Scorecard]:
    key = (site.base_url, site.fetched_at, site.kind)
    cache = st.session_state.setdefault("analysis_cache", {})
    if key not in cache:
        result = run_checks(site)
        cache[key] = (result, score(result, len(site.pages)))
    return cache[key]


def site_banner(site: Site) -> None:
    if site.kind == "live":
        st.success(f"Live scan of {site.base_url}: {len(site.pages)} pages read on {site.fetched_at[:10]}.")
    else:
        st.info("Showing a saved, text-only snapshot of cynbit.in (30 Oct 2026, paraphrased). "
                "Choose 'Scan a live website' in the sidebar to check the real pages, including titles, "
                "alt text, links and forms.")
