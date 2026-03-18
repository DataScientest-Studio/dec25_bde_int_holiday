"""
Data Quality Metrics page.
"""
import streamlit as st
import requests
import pandas as pd
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="Data Quality", layout="wide")
st.title("🔍 Data Quality Metrics")
st.markdown("Missing/null fields analysis")

def fetch_quality():
    """Fetch data quality metrics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/quality", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching quality metrics: {str(e)}")
        return None

def fetch_stats():
    """Fetch statistics from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return None

with st.spinner("Loading quality metrics..."):
    quality = fetch_quality()

if quality:
    if isinstance(quality, dict) and quality:
        # Convert to list of dicts for DataFrame
        quality_list = [
            {"Field": field_name.replace("_", " ").title(), "Missing Count": count}
            for field_name, count in quality.items()
        ]
        df = pd.DataFrame(quality_list)
        
        if not df.empty:
            st.header("Missing Fields Summary")
            st.bar_chart(df.set_index("Field"))
            
            st.header("Data Table")
            st.dataframe(df, width='stretch', hide_index=True)
            
            # Calculate total POIs for percentage
            stats = fetch_stats()
            total = stats.get("total_pois", 1) if stats else 1
            
            if total > 0:
                st.header("Completeness Percentage")
                df_pct = df.copy()
                df_pct["Completeness %"] = ((total - df_pct["Missing Count"]) / total * 100).round(2)
                st.dataframe(df_pct[["Field", "Completeness %"]], width='stretch', hide_index=True)
        else:
            st.info("No quality data available.")
    else:
        st.warning("Invalid quality data format received.")
else:
    st.warning("Failed to load quality metrics.")