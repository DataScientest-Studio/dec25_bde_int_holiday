from pathlib import Path
import base64

import streamlit as st

st.set_page_config(page_title="Holiday Itinerary - Presentation", layout="wide")

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"

st.title("Holiday Itinerary — Data Engineering Project")
st.caption("Presentation app (docs-driven). Use the sidebar to open the Final Report and slides.")

if not DOCS_DIR.exists():
    st.error("docs/ folder not found. This app expects a ./docs directory next to streamlit_app.py")
    st.stop()

# --- Background image (prefer docs/background.jpg) ---
bg_candidates = [
    DOCS_DIR / "background.jpg",
    DOCS_DIR / "background.jpeg",
    DOCS_DIR / "background.png",
    DOCS_DIR / "architecture_kubernetes.png",
    DOCS_DIR / "architecture_kubernetes.jpg",
    DOCS_DIR / "architecture_kubernetes.jpeg",
    DOCS_DIR / "architecture.png",
    DOCS_DIR / "architecture.jpg",
    DOCS_DIR / "erd.png",
]

bg_img = next((p for p in bg_candidates if p.exists()), None)


def set_background(image_path: Path, opacity: float = 0.16):
    """Set a full-page background image with a white overlay for readability."""
    encoded = base64.b64encode(image_path.read_bytes()).decode()
    ext = image_path.suffix.lower().lstrip(".")
    mime = "png" if ext == "png" else "jpeg"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
              linear-gradient(rgba(255,255,255,{1-opacity}), rgba(255,255,255,{1-opacity})),
              url("data:image/{mime};base64,{encoded}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


if bg_img:
    set_background(bg_img, opacity=0.18)
# NOTE: intentionally no "Background: ..." text on the page


st.markdown(
    """
### Team
- Munir Al Tawil  
- Roxana Miu  
- Ulrich Kitieu  

**Date:** 23 March 2026
"""
)

st.markdown(
    """
### How to navigate
- **Final Report** 
- **Slides**: 
- **Doc Viewer**:
"""
)