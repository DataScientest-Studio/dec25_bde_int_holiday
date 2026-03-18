"""
Streamlit dashboard for POI data visualization.
Main entry point with navigation to multiple pages.
"""
import streamlit as st
import os
import logging
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API base URL - use environment variable or default
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
# In Docker, use service name
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

# Page configuration
st.set_page_config(
    page_title="POI Analytics Dashboard",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar header
st.sidebar.title("📍 POI Dashboard")
st.sidebar.markdown("---")

# API Health check function
def check_api_health():
    """Check API health and database connectivity."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return response.json()
        return {"status": "unhealthy", "api": "error", "database": {"status": "unknown"}}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"API connection error: {str(e)}")
        return {"status": "unreachable", "api": "error", "database": {"status": "unknown"}, "error": f"Cannot connect to {API_BASE_URL}"}
    except Exception as e:
        logger.error(f"API health check error: {str(e)}")
        return {"status": "unreachable", "api": "error", "database": {"status": "unknown"}, "error": str(e)}

# Check API connection and database status
health_status = check_api_health()

# Display health status in sidebar
st.sidebar.header("System Status")
if health_status.get("status") == "healthy":
    st.sidebar.success("✅ API: Healthy")
    db_status = health_status.get("database", {}).get("status", "unknown")
    if db_status == "connected":
        st.sidebar.success("✅ Database: Connected")
    else:
        st.sidebar.error(f"❌ Database: {db_status}")
        if health_status.get("database", {}).get("error"):
            st.sidebar.caption(health_status["database"]["error"])
elif health_status.get("status") == "unreachable":
    st.sidebar.error("❌ API: Unreachable")
    st.error(f"⚠️ Cannot connect to API at {API_BASE_URL}")
    st.info("Please ensure the FastAPI server is running.")
    if not os.getenv("DOCKER_ENV"):
        st.code("py -m uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000", language="bash")
    st.stop()
else:
    st.sidebar.warning("⚠️ API: Unhealthy")
    db_status = health_status.get("database", {}).get("status", "unknown")
    st.sidebar.error(f"❌ Database: {db_status}")
    if health_status.get("database", {}).get("error"):
        st.sidebar.caption(health_status["database"]["error"])
    st.warning("API is responding but database connection failed. Some features may not work.")

st.sidebar.markdown("---")

# Title and info
st.title("📊 POI Analytics Dashboard")
st.markdown("""
Welcome to the comprehensive POI (Point of Interest) Analytics Dashboard!

Use the navigation menu on the left to explore different sections:
- **📊 Overview** - Key statistics and performance indicators
- **📈 Types Chart** - Distribution of POI types
- **📅 Updates Chart** - Historical update trends
- **🔍 Data Quality** - Data completeness metrics
- **🔎 POI Explorer** - Browse and search POIs
- **🗺️ Map Explorer** - Interactive map visualization
- **🗺️ Itinerary Builder** - AI-powered itinerary generation
- **📅 Itinerary Analysis** - ML clustering and predictions
- **🕸️ Graph** - Neo4j graph database statistics
""")

st.info("👈 Select a page from the sidebar to get started!")