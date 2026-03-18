from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Project Presentation", layout="wide")

DOCS_DIR = Path(__file__).resolve().parent / "docs"

st.title("Project Presentation (from /docs)")
st.caption(f"Docs folder: {DOCS_DIR}")

if not DOCS_DIR.exists():
    st.error("docs/ folder not found. This app expects a ./docs directory next to streamlit_app.py")
    st.stop()

st.markdown(
    """
This Streamlit app renders documentation directly from the `docs/` folder.

Use the pages in the sidebar:
- **Doc Viewer**: browse and open any docs file
- **Slide Mode**: step through a curated order like a presentation
"""
)

md_files = sorted([p for p in DOCS_DIR.glob("*") if p.is_file() and p.suffix.lower() in {".md", ".mdtxt"}])
img_files = sorted([p for p in DOCS_DIR.glob("*") if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}])

c1, c2 = st.columns(2)

with c1:
    st.markdown("### Markdown docs")
    for p in md_files:
        st.write(f"- {p.name}")

with c2:
    st.markdown("### Images")
    for p in img_files:
        st.write(f"- {p.name}")