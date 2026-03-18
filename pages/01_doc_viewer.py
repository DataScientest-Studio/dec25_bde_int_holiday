from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Doc Viewer", layout="wide")

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

st.title("Doc Viewer")

if not DOCS_DIR.exists():
    st.error("docs/ folder not found.")
    st.stop()

def is_supported(path: Path) -> bool:
    return path.suffix.lower() in {".md", ".mdtxt", ".png", ".jpg", ".jpeg", ".puml", ".py", ".txt"}

files = sorted([p for p in DOCS_DIR.glob("*") if p.is_file() and is_supported(p)])

with st.sidebar:
    st.header("Files in docs/")
    selected = st.selectbox("Open file", [p.name for p in files])

path = DOCS_DIR / selected
st.caption(f"Viewing: {path}")

suffix = path.suffix.lower()

if suffix in {".md", ".mdtxt"}:
    text = path.read_text(encoding="utf-8", errors="replace")
    st.markdown(text)
elif suffix in {".png", ".jpg", ".jpeg"}:
    st.image(str(path), use_container_width=True)
elif suffix in {".puml", ".py", ".txt"}:
    st.code(path.read_text(encoding="utf-8", errors="replace"), language="text")
else:
    st.info("Unsupported file type.")