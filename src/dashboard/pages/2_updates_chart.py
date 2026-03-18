"""
POI Updates Over Time page.
"""
import streamlit as st
import requests
import pandas as pd
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="Updates Chart", layout="wide")
st.title("📅 POI Updates Over Time")

def fetch_updates_chart(days: int = 30):
    """Fetch update counts from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/charts/updates", params={"days": days}, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching updates chart: {str(e)}")
        return None

days = st.sidebar.slider("Number of days", 7, 90, 30)

with st.spinner("Loading update counts..."):
    update_data = fetch_updates_chart(days=days)

if update_data:
    df = pd.DataFrame(update_data)
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")
        
        st.line_chart(df.set_index("date"))
        
        st.header("Data Table")
        st.dataframe(df, width='stretch', hide_index=True)
    else:
        st.info("No update data available.")
else:
    st.warning("Failed to load update data.")