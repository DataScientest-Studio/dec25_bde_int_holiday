from __future__ import annotations

from pathlib import Path
import base64
import zlib

import requests
import streamlit as st

st.set_page_config(page_title="Holiday Itinerary - Presentation", layout="wide")

ROOT = Path(__file__).resolve().parent
DOCS_DIR = ROOT / "docs"
SCREENSHOTS_DIR_CANDIDATES = [
    DOCS_DIR / "screenshots",
    ROOT / "screenshots",
]

st.title("Holiday Itinerary — Data Engineering Project")

if not DOCS_DIR.exists():
    st.error("docs/ folder not found. This app expects a ./docs directory next to streamlit_app.py")
    st.stop()

# --- Background image (prefer docs/background.*) ---
bg_candidates = [
    DOCS_DIR / "background.jpg",
    DOCS_DIR / "background.jpeg",
    DOCS_DIR / "background.png",
]
bg_img = next((p for p in bg_candidates if p.exists()), None)


def set_background(image_path: Path, opacity: float = 0.16):
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


def render_file(path: Path):
    suffix = path.suffix.lower()

    if suffix in {".md", ".mdtxt"}:
        st.markdown(path.read_text(encoding="utf-8", errors="replace"))
        return

    if suffix in {".png", ".jpg", ".jpeg", ".svg"}:
        st.image(str(path), use_container_width=True)
        return

    if suffix == ".puml":
        # Default behavior for Details: show source (Architecture page renders as graph)
        st.code(path.read_text(encoding="utf-8", errors="replace"), language="text")
        return

    st.code(path.read_text(encoding="utf-8", errors="replace"), language="text")


def list_files(root: Path, extensions: set[str]) -> list[Path]:
    if not root.exists():
        return []
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in extensions]
    files.sort(key=lambda p: str(p.relative_to(root)).lower())
    return files


def pick_first_existing(candidates: list[Path]) -> Path | None:
    return next((p for p in candidates if p.exists()), None)


def plantuml_deflate_encode(plantuml_text: str) -> str:
    """
    Encode PlantUML text for the PlantUML server URL.
    """
    # PlantUML uses raw DEFLATE (no zlib header / checksum)
    data = zlib.compress(plantuml_text.encode("utf-8"))[2:-4]

    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"

    def encode6bit(b: int) -> str:
        return alphabet[b & 0x3F]

    def append3bytes(b1: int, b2: int, b3: int) -> str:
        c1 = b1 >> 2
        c2 = ((b1 & 0x3) << 4) | (b2 >> 4)
        c3 = ((b2 & 0xF) << 2) | (b3 >> 6)
        c4 = b3 & 0x3F
        return encode6bit(c1) + encode6bit(c2) + encode6bit(c3) + encode6bit(c4)

    res = []
    i = 0
    while i < len(data):
        b1 = data[i]
        b2 = data[i + 1] if i + 1 < len(data) else 0
        b3 = data[i + 2] if i + 2 < len(data) else 0
        res.append(append3bytes(b1, b2, b3))
        i += 3
    return "".join(res)


def render_puml_as_svg(puml_path: Path):
    """
    Render a .puml file as an SVG using the public PlantUML server.
    Falls back to showing the PlantUML source if rendering fails.
    """
    text = puml_path.read_text(encoding="utf-8", errors="replace")
    encoded = plantuml_deflate_encode(text)
    url = f"https://www.plantuml.com/plantuml/svg/{encoded}"

    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        st.markdown(r.text, unsafe_allow_html=True)  # inline SVG
    except Exception as e:
        st.warning(f"Could not render {puml_path.name} as diagram ({e}). Showing source instead.")
        st.code(text, language="text")


if bg_img:
    set_background(bg_img, opacity=0.18)

# --- Sidebar navigation ---
st.sidebar.title("Presentation")

page = st.sidebar.radio(
    "Page",
    ["Final Report", "Architecture", "Details", "Screenshots"],
    index=0,  # Final Report is the landing page
)

# Final report: your repo has docs/final_report.mdtxt (verified)
FINAL_REPORT_CANDIDATES = [
    DOCS_DIR / "final_report.mdtxt",
]

# Architecture curated slide deck (exact files you requested)
ARCHITECTURE_ITEMS: list[tuple[str, Path]] = [
    ("Architecture (Compose / services)", DOCS_DIR / "architecture.png"),
    ("Architecture (Kubernetes)", DOCS_DIR / "architecture_kubernetes.png"),
    ("ERD (PlantUML)", DOCS_DIR / "erd.puml"),
    ("ERD (PNG)", DOCS_DIR / "Holiday_Itinerary_PostgreSQL_ERD.png"),
    ("Architecture Diagram (Markdown)", DOCS_DIR / "ARCHITECTURE_DIAGRAM.md"),
]

# Details mode: show everything in docs/ EXCEPT:
# - architecture curated items
# - final report file(s)
# - screenshots folder
DETAIL_EXTS = {".md", ".mdtxt", ".png", ".jpg", ".jpeg", ".svg", ".puml"}

# Screenshots are separate (keep jpg/jpeg allowed)
SCREENSHOT_EXTS = {".png", ".jpg", ".jpeg", ".svg"}


def is_excluded_from_details(p: Path) -> bool:
    # exclude final report candidates
    final_paths = {c.resolve() for c in FINAL_REPORT_CANDIDATES if c.exists()}
    if p.resolve() in final_paths:
        return True

    # exclude screenshots subtree
    screenshots_root = (DOCS_DIR / "screenshots").resolve()
    try:
        if p.resolve().is_relative_to(screenshots_root):
            return True
    except AttributeError:
        # Python < 3.9 fallback
        if str(screenshots_root) in str(p.resolve()):
            return True

    # exclude architecture curated items
    arch_paths = {path.resolve() for _, path in ARCHITECTURE_ITEMS if path.exists()}
    if p.resolve() in arch_paths:
        return True

    return False


# --- Content rendering ---
if page == "Final Report":
    report = pick_first_existing(FINAL_REPORT_CANDIDATES)
    if not report:
        st.error("Final report not found in docs/. Expected docs/final_report.mdtxt")
    else:
        render_file(report)

elif page == "Architecture":
    st.subheader("Architecture")

    existing_items = [(label, path) for (label, path) in ARCHITECTURE_ITEMS if path.exists()]
    missing_items = [(label, path) for (label, path) in ARCHITECTURE_ITEMS if not path.exists()]

    if missing_items:
        with st.expander(""):
            for label, path in missing_items:
                st.write(f"- {label}: {path}")

    if not existing_items:
        st.warning(
            "No architecture files found in docs/. Expected files like:\n"
            "- docs/architecture.png\n"
            "- docs/architecture_kubernetes.png\n"
            "- docs/erd.puml\n"
            "- docs/Holiday_Itinerary_PostgreSQL_ERD.png\n"
            "- docs/ARCHITECTURE_DIAGRAM.md"
        )
        st.stop()

    labels = [label for label, _ in existing_items]
    choice = st.sidebar.selectbox("Architecture section", labels, index=0)
    chosen = dict(existing_items)[choice]

    if chosen.suffix.lower() == ".puml":
        render_puml_as_svg(chosen)
    else:
        render_file(chosen)

elif page == "Details":
    st.subheader("Details (any file or explanation that contributed to our decisions)")

    all_docs = list_files(DOCS_DIR, DETAIL_EXTS)
    docs = [p for p in all_docs if not is_excluded_from_details(p)]

    if not docs:
        st.warning("No documents found in Details view after exclusions.")
        st.stop()

    labels = [str(p.relative_to(DOCS_DIR)) for p in docs]
    choice = st.sidebar.selectbox("Document", labels, index=0)
    render_file(DOCS_DIR / choice)

else:  # Screenshots
    st.subheader("Screenshots")

    screenshots_dir = pick_first_existing(SCREENSHOTS_DIR_CANDIDATES)
    if not screenshots_dir:
        st.warning(
            "Screenshots folder not found. Create one of:\n- docs/screenshots/\n- screenshots/\n"
            "and add .png/.jpg files."
        )
        st.stop()

    shots = list_files(screenshots_dir, SCREENSHOT_EXTS)

    if not shots:
        st.warning(f"No screenshots found in {screenshots_dir}. Add .png/.jpg files.")
        st.stop()

    labels = [str(p.relative_to(screenshots_dir)) for p in shots]
    choice = st.sidebar.selectbox("Screenshot", labels, index=0)
    render_file(screenshots_dir / choice)