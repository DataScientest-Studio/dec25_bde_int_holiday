"""
Overview page showing key statistics and KPIs.
"""
import streamlit as st
import requests
import pandas as pd
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="Overview", layout="wide")
st.title("📊 Overview - Key Performance Indicators")

# Debug info
with st.expander("🔧 Debug Info", expanded=False):
    st.write(f"**API Base URL:** {API_BASE_URL}")
    st.write(f"**Docker Environment:** {os.getenv('DOCKER_ENV', 'Not set')}")
    
    # Test API connection
    try:
        test_response = requests.get(f"{API_BASE_URL}/", timeout=2)
        st.success(f"✅ API is reachable (Status: {test_response.status_code})")
    except Exception as e:
        st.error(f"❌ API connection test failed: {str(e)}")

def fetch_stats():
    """Fetch statistics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching stats: {str(e)}")
        return None

with st.spinner("Loading statistics..."):
    stats = fetch_stats()

if stats is None:
    st.warning("⚠️ No statistics data available.")
    st.info(f"""
    **Troubleshooting Steps:**
    1. Check if API is running: Visit {API_BASE_URL}/docs
    2. Check API health: Visit {API_BASE_URL}/health
    3. Check browser console for CORS errors (F12 → Console)
    4. Verify API_BASE_URL is correct: {API_BASE_URL}
    5. Try manually calling: {API_BASE_URL}/stats in your browser
    """)
    st.stop()

# Display KPIs
st.header("Key Metrics")
col1, col2, col3, col4 = st.columns(4)

total_pois = stats.get("total_pois", 0)
pois_with_coords = stats.get("pois_with_coordinates", 0)
distinct_types = stats.get("distinct_types", 0)

with col1:
    st.metric("Total POIs", total_pois)

with col2:
    st.metric("With Coordinates", pois_with_coords)

with col3:
    st.metric("Distinct Types", distinct_types)

with col4:
    last_update = stats.get("last_update_max")
    if last_update:
        st.metric("Latest Update", pd.to_datetime(last_update).strftime("%Y-%m-%d"))
    else:
        st.metric("Latest Update", "N/A")

# Show warning if all metrics are zero
if total_pois == 0 and pois_with_coords == 0 and distinct_types == 0:
    st.warning("⚠️ All metrics are zero. The database may be empty. Run the ETL pipeline to load data.")

# Additional info
st.header("Update Range")
col1, col2 = st.columns(2)

with col1:
    min_update = stats.get("last_update_min")
    if min_update:
        st.info(f"**Earliest:** {pd.to_datetime(min_update).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info("**Earliest:** N/A")

with col2:
    max_update = stats.get("last_update_max")
    if max_update:
        st.info(f"**Latest:** {pd.to_datetime(max_update).strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info("**Latest:** N/A")