"""
POI Explorer page - browse and search POIs.
"""
import streamlit as st
import requests
import pandas as pd
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="POI Explorer", layout="wide")
st.title("🔎 POI Explorer")
st.markdown("Browse and search POIs with filters and pagination")

def fetch_pois(limit: int = 100, offset: int = 0, type_filter=None, search=None):
    """Fetch POIs from API."""
    try:
        params = {"limit": limit, "offset": offset}
        if type_filter:
            params["type"] = type_filter
        if search:
            params["search"] = search
        
        response = requests.get(f"{API_BASE_URL}/pois", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching POIs: {str(e)}")
        return None

# Filters in sidebar
st.sidebar.header("Filters")
search_term = st.sidebar.text_input("Search (label/description)", "")
type_filter = st.sidebar.text_input("Filter by type", "")

# Pagination
st.sidebar.header("Pagination")
page_size = st.sidebar.selectbox("Items per page", [25, 50, 100, 200], index=1)

# Get current page from session state
if "poi_page" not in st.session_state:
    st.session_state.poi_page = 0

col1, col2, col3 = st.sidebar.columns(3)
with col1:
    if st.button("◀ Prev"):
        if st.session_state.poi_page > 0:
            st.session_state.poi_page -= 1
with col2:
    st.write(f"Page {st.session_state.poi_page + 1}")
with col3:
    if st.button("Next ▶"):
        st.session_state.poi_page += 1

offset = st.session_state.poi_page * page_size

# Fetch POIs
with st.spinner("Loading POIs..."):
    poi_data = fetch_pois(
        limit=page_size,
        offset=offset,
        type_filter=type_filter if type_filter else None,
        search=search_term if search_term else None
    )

if poi_data:
    items = poi_data.get("items", [])
    total = poi_data.get("total", 0)
    
    st.info(f"Showing {len(items)} of {total} POIs")
    
    if items:
        df = pd.DataFrame(items)
        
        # Format datetime columns
        for col in ["last_update", "created_at"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Select display columns
        display_cols = ["id", "label", "type", "city", "latitude", "longitude", "last_update"]
        available_cols = [col for col in display_cols if col in df.columns]
        
        st.dataframe(df[available_cols], width='stretch', hide_index=True)
        
        # Reset page if needed
        max_pages = (total + page_size - 1) // page_size
        if st.session_state.poi_page >= max_pages:
            st.session_state.poi_page = max(0, max_pages - 1)
    else:
        st.info("No POIs found matching the criteria.")
else:
    st.warning("Failed to load POIs.")