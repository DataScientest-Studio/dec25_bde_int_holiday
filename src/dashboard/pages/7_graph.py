"""
Graph Database (Neo4j) page.
"""
import streamlit as st
import requests
import pandas as pd
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="Graph Database", layout="wide")
st.title("🕸️ Graph Database (Neo4j)")
st.markdown("Neo4j graph database statistics and model information")

def fetch_graph_summary():
    """Fetch graph summary from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/graph/summary", timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 503:
            return None
        st.error(f"Error fetching graph summary: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error fetching graph summary: {str(e)}")
        return None

with st.spinner("Loading graph summary..."):
    graph_summary = fetch_graph_summary()

if graph_summary:
    st.header("Graph Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("POI Nodes", graph_summary.get("poi_nodes", 0))
    
    with col2:
        st.metric("Type Nodes", graph_summary.get("type_nodes", 0))
    
    with col3:
        st.metric("City Nodes", graph_summary.get("city_nodes", 0))
    
    with col4:
        st.metric("Department Nodes", graph_summary.get("department_nodes", 0))
    
    st.header("Relationships")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("HAS_TYPE", graph_summary.get("has_type_relationships", 0))
    
    with col2:
        st.metric("IN_CITY", graph_summary.get("in_city_relationships", 0))
    
    with col3:
        st.metric("IN_DEPARTMENT", graph_summary.get("in_department_relationships", 0))
    
    st.header("Totals")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Nodes", graph_summary.get("total_nodes", 0))
    
    with col2:
        st.metric("Total Relationships", graph_summary.get("total_relationships", 0))
    
    st.header("Graph Model")
    st.info("""
    The Neo4j graph database models POI data with the following structure:

    **Nodes:**
    - `POI`: Points of Interest with properties (id, label, type, latitude, longitude, uri, last_update)
    - `Type`: POI types (e.g., Museum, Restaurant, Hotel)
    - `City`: Cities where POIs are located (optional)
    - `Department`: French departments where POIs are located (optional)

    **Relationships:**
    - `(:POI)-[:HAS_TYPE]->(:Type)`: Links POIs to their types
    - `(:POI)-[:IN_CITY]->(:City)`: Links POIs to cities
    - `(:POI)-[:IN_DEPARTMENT]->(:Department)`: Links POIs to departments

    **Why Graph Database?**
    Graph databases excel at relationship queries and enable powerful graph analytics!
    """)
    
    st.header("Detailed Statistics")
    summary_df = pd.DataFrame([
        {"Metric": "POI Nodes", "Count": graph_summary.get("poi_nodes", 0)},
        {"Metric": "Type Nodes", "Count": graph_summary.get("type_nodes", 0)},
        {"Metric": "City Nodes", "Count": graph_summary.get("city_nodes", 0)},
        {"Metric": "Department Nodes", "Count": graph_summary.get("department_nodes", 0)},
        {"Metric": "HAS_TYPE Relationships", "Count": graph_summary.get("has_type_relationships", 0)},
        {"Metric": "IN_CITY Relationships", "Count": graph_summary.get("in_city_relationships", 0)},
        {"Metric": "IN_DEPARTMENT Relationships", "Count": graph_summary.get("in_department_relationships", 0)},
        {"Metric": "Total Nodes", "Count": graph_summary.get("total_nodes", 0)},
        {"Metric": "Total Relationships", "Count": graph_summary.get("total_relationships", 0)},
    ])
    st.dataframe(summary_df, width='stretch', hide_index=True)

else:
    st.warning("⚠️ Neo4j graph database is unavailable.")
    st.info("""
    The graph database may not be running or may not have been loaded yet.

    **To load data into Neo4j:**
    1. Ensure Neo4j service is running: `docker compose ps neo4j`
    2. Run the graph loader: `docker compose exec holiday_scheduler python -m src.pipelines.run_graph_load`
    3. Or wait for the scheduled hourly ETL to complete

    **Access Neo4j Browser:**
    - URL: http://localhost:7474
    """)