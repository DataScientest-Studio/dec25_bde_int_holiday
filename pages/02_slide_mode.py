from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Slide Mode", layout="wide")

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

st.title("Slide Mode (Presentation)")

if not DOCS_DIR.exists():
    st.error("docs/ folder not found.")
    st.stop()

# Curated presentation order (edit as you like)
SLIDES = [
    "architecture.md",
    "ARCHITECTURE_DIAGRAM.md",
    "schema.md",
    "GRAPH_MODEL.md",
    "data_sources.md",
    "explaining_ml.mdtxt",
    "ITINERARY_BUILDER.md",
    "IMPLEMENTATION_SUMMARY.md",
    "PROFESSOR_REQUIREMENTS_CHECKLIST.md",
    "PROGRESS_REPORT.md",
    "FINAL_AUDIT_REPORT.md",
    "GAP_ANALYSIS.md",
    "GAP_PLAN.md",
    "architecture_kubernetes.png",
    "erd.png",
]

existing = [s for s in SLIDES if (DOCS_DIR / s).exists()]
missing = [s for s in SLIDES if not (DOCS_DIR / s).exists()]

if missing:
    with st.expander("Missing slide files (not found in docs/)", expanded=False):
        for s in missing:
            st.write(f"- {s}")

if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

with st.sidebar:
    st.header("Navigation")
    idx = st.session_state.slide_idx
    st.write(f"Slide {idx + 1} / {len(existing)}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("◀ Prev", use_container_width=True, disabled=(idx <= 0)):
            st.session_state.slide_idx = max(0, idx - 1)
            st.rerun()
    with col2:
        if st.button("Next ▶", use_container_width=True, disabled=(idx >= len(existing) - 1)):
            st.session_state.slide_idx = min(len(existing) - 1, idx + 1)
            st.rerun()

    st.divider()
    jump = st.selectbox("Jump to slide", list(range(1, len(existing) + 1)), index=st.session_state.slide_idx)
    if (jump - 1) != st.session_state.slide_idx:
        st.session_state.slide_idx = jump - 1
        st.rerun()

slide_name = existing[st.session_state.slide_idx]
path = DOCS_DIR / slide_name

st.subheader(slide_name)

suffix = path.suffix.lower()
if suffix in {".md", ".mdtxt"}:
    st.markdown(path.read_text(encoding="utf-8", errors="replace"))
elif suffix in {".png", ".jpg", ".jpeg"}:
    st.image(str(path), use_container_width=True)
else:
    st.code(path.read_text(encoding="utf-8", errors="replace"), language="text")