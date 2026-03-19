from pathlib import Path

import streamlit as st

st.set_page_config(page_title="Screenshots", layout="wide")

ROOT = Path(__file__).resolve().parent.parent
SCREEN_DIR = ROOT / "docs" / "screenshots"

st.title("Screenshots")
st.caption("Gallery of screenshots used in the presentation / report.")

if not SCREEN_DIR.exists():
    st.warning("No screenshots folder found.")
    st.info("Create it with: docs/screenshots/ and add .png/.jpg images.")
    st.stop()

images = []
for ext in ("*.png", "*.jpg", "*.jpeg"):
    images.extend(SCREEN_DIR.glob(ext))
images = sorted(images)

if not images:
    st.warning("No images found in docs/screenshots/")
    st.stop()

# Optional filter/search
query = st.text_input("Filter by filename (optional)", value="").strip().lower()
if query:
    images = [p for p in images if query in p.name.lower()]

# Layout options
cols = st.slider("Columns", min_value=1, max_value=4, value=2)

# Render as grid
rows = [images[i : i + cols] for i in range(0, len(images), cols)]
for row in rows:
    col_objs = st.columns(len(row))
    for c, img_path in zip(col_objs, row):
        with c:
            st.image(str(img_path), use_container_width=True)
            st.caption(img_path.name)

# Optional: click-to-open full size (simple list)
with st.expander("Open a screenshot full-size", expanded=False):
    selected = st.selectbox("Choose a screenshot", [p.name for p in images])
    chosen = SCREEN_DIR / selected
    st.image(str(chosen), use_container_width=True)