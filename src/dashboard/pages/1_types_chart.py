"""
POI Types Chart page.
"""
import streamlit as st
import requests
import pandas as pd
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="Types Chart", layout="wide")
st.title("📈 POI Counts by Type")

def fetch_types_chart(limit: int = 15):
    """Fetch type counts from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/charts/types", params={"limit": limit}, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching types chart: {str(e)}")
        return None

limit = st.sidebar.slider("Number of types to show", 5, 50, 15)

with st.spinner("Loading type counts..."):
    type_data = fetch_types_chart(limit=limit)

if type_data:
    df = pd.DataFrame(type_data)
    if not df.empty:
        st.bar_chart(df.set_index("type"))
        
        st.header("Data Table")
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No type data available.")
else:
    st.warning("Failed to load type data.")