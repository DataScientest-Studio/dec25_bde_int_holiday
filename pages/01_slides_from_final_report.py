from pathlib import Path
import streamlit as st

st.set_page_config(page_title="Slides (Final Report Order)", layout="wide")

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"

st.title("Slides — Ordered like the Final Report")
st.caption("This page steps through key docs/images in the same narrative order as docs/final_report.mdtxt.")

if not DOCS_DIR.exists():
    st.error("docs/ folder not found.")
    st.stop()

SLIDES = [
    # 1) Executive Summary / Architecture overview
    "architecture.md",
    "ARCHITECTURE_DIAGRAM.md",
    "architecture_kubernetes.png"
    "architecture.png",

    # 5) Data modeling decisions
    "schema.md",
    "Holiday_Itinerary_PostgreSQL_ERD.png",

    # 6) ETL design + graph loader
    "data_sources.md",
    "GRAPH_MODEL.md",

    # Optional: other project reports / evidence
    "IMPLEMENTATION_SUMMARY.md",
    "PROFESSOR_REQUIREMENTS_CHECKLIST.md",
    "PROGRESS_REPORT.md",
    "FINAL_AUDIT_REPORT.md",
    "GAP_ANALYSIS.md",
    "GAP_PLAN.md",
    "deploying_kubernetes_explained.mdtxt",
]

existing = [s for s in SLIDES if (DOCS_DIR / s).exists()]
missing = [s for s in SLIDES if not (DOCS_DIR / s).exists()]

if missing:
    with st.expander("Missing slide assets (not found in docs/)", expanded=False):
        for m in missing:
            st.write(f"- {m}")

if not existing:
    st.warning("No slide assets found. Check the SLIDES list and your docs/ folder.")
    st.stop()

# navigation
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

col1, _, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("◀ Prev", use_container_width=True) and st.session_state.slide_idx > 0:
        st.session_state.slide_idx -= 1
with col3:
    if st.button("Next ▶", use_container_width=True) and st.session_state.slide_idx < len(existing) - 1:
        st.session_state.slide_idx += 1

current = existing[st.session_state.slide_idx]
current_path = DOCS_DIR / current

st.markdown(f"### {st.session_state.slide_idx + 1}/{len(existing)} — `{current}`")

suffix = current_path.suffix.lower()
if suffix in {".png", ".jpg", ".jpeg"}:
    st.image(str(current_path), width="stretch")
elif suffix in {".md", ".mdtxt"}:
    st.markdown(current_path.read_text(encoding="utf-8"))
elif suffix == ".puml":
    st.code(current_path.read_text(encoding="utf-8"), language="plantuml")
else:
    st.code(current_path.read_text(encoding="utf-8", errors="replace"))