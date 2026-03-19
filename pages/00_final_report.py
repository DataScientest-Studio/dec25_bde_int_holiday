from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Final Report", layout="wide")

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
FINAL_REPORT = DOCS_DIR / "final_report.mdtxt"

st.title("Final Report")

st.markdown(
    """
**Team:** Munir Al Tawil · Roxana Miu · Ulrich Kitieu  
**Date:** 23 March 2026
"""
)

if not DOCS_DIR.exists():
    st.error("docs/ folder not found.")
    st.stop()

if not FINAL_REPORT.exists():
    st.error("docs/final_report.mdtxt not found.")
    st.stop()

st.markdown(FINAL_REPORT.read_text(encoding="utf-8"))