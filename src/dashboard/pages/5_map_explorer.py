"""
Map Explorer page - interactive map visualization.
"""
import streamlit as st
import requests
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
if os.getenv("DOCKER_ENV"):
    API_BASE_URL = "http://api:8000"

st.set_page_config(page_title="Map Explorer", layout="wide")
st.title("🗺️ Map Explorer")
st.markdown("Interactive map visualization of POIs")

def fetch_geojson(limit: int = 1000, offset: int = 0, type_filter=None, search=None, bbox=None):
    """Fetch GeoJSON data from API."""
    try:
        params = {"limit": limit, "offset": offset}
        if type_filter:
            params["type"] = type_filter
        if search:
            params["search"] = search
        if bbox:
            params["bbox"] = bbox
        
        response = requests.get(f"{API_BASE_URL}/pois/geojson", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching GeoJSON: {str(e)}")
        return None

def fetch_categories():
    """Fetch POI categories from API."""
    try:
        response = requests.get(f"{API_BASE_URL}/stats/categories", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching categories: {str(e)}")
        return None

# Sidebar filters
st.sidebar.header("Map Filters")

# Fetch categories for type dropdown
categories_data = fetch_categories()
type_options = ["All"] + ([cat["category"] for cat in categories_data] if categories_data else [])
selected_type = st.sidebar.selectbox("Filter by Type", type_options, index=0)

search_input = st.sidebar.text_input("Search (label/description)", "")

limit_slider = st.sidebar.slider("Max Items", 100, 5000, 1000, step=100)

cluster_markers = st.sidebar.toggle("Cluster Markers", value=True)

# Map bounds filter button
st.sidebar.header("Map Bounds Filter")
filter_by_bounds = st.sidebar.button("Filter by visible map")

# Initialize session state for map bounds
if "current_bbox" not in st.session_state:
    st.session_state.current_bbox = None

# Prepare filters
type_filter = None if selected_type == "All" else selected_type
search_filter = search_input if search_input else None
bbox_filter = st.session_state.current_bbox if filter_by_bounds and st.session_state.current_bbox else None

# Fetch GeoJSON data
with st.spinner("Loading POIs on map..."):
    geojson_data = fetch_geojson(
        limit=limit_slider,
        offset=0,
        type_filter=type_filter,
        search=search_filter,
        bbox=bbox_filter
    )

if geojson_data:
    features = geojson_data.get("features", [])
    
    if features:
        # Calculate KPI metrics
        total_items = len(features)
        distinct_types = len(set(
            f.get("properties", {}).get("type")
            for f in features
            if f.get("properties", {}).get("type")
        ))
        
        # Display KPIs
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Items Shown", total_items)
        with col2:
            st.metric("Distinct Types", distinct_types)
        
        # Calculate map center and bounds from data
        lats = [f["geometry"]["coordinates"][1] for f in features]
        lons = [f["geometry"]["coordinates"][0] for f in features]
        
        if lats and lons:
            center_lat = sum(lats) / len(lats)
            center_lon = sum(lons) / len(lons)
            
            # Create map
            m = folium.Map(
                location=[center_lat, center_lon],
                zoom_start=6,
                tiles="OpenStreetMap"
            )
            
            # Add markers
            if cluster_markers:
                marker_cluster = MarkerCluster().add_to(m)
                marker_group = marker_cluster
            else:
                marker_group = m
            
            for feature in features:
                coords = feature["geometry"]["coordinates"]
                lon, lat = coords[0], coords[1]
                props = feature.get("properties", {})
                
                # Safe text field extraction
                safe_label = (props.get("label") or "").strip()
                safe_desc = (props.get("description") or "").strip()
                safe_type = (props.get("type") or "N/A").strip()
                safe_uri = (props.get("uri") or "").strip()
                safe_last_update = props.get("last_update") or "N/A"
                
                if not safe_label and not safe_desc:
                    safe_label = "No description available"
                
                desc_truncated = (safe_desc[:200] + "…") if len(safe_desc) > 200 else safe_desc
                
                popup_html = f"""
                <div style="width: 250px;">
                    <h4 style="margin: 0 0 10px 0; font-weight: bold;">{safe_label}</h4>
                    <p style="margin: 5px 0;"><strong>Type:</strong> {safe_type}</p>
                    <p style="margin: 5px 0;"><strong>Updated:</strong> {safe_last_update}</p>
                    {f'<p style="margin: 5px 0;"><strong>Description:</strong> {desc_truncated}</p>' if safe_desc else ''}
                    {f'<p style="margin: 5px 0;"><a href="{safe_uri}" target="_blank">View Details</a></p>' if safe_uri else ''}
                </div>
                """
                
                popup = folium.Popup(popup_html, max_width=300)
                folium.Marker(
                    location=[lat, lon],
                    popup=popup,
                    tooltip=safe_label or "POI"
                ).add_to(marker_group)
            
            # Display map and get bounds
            map_data = st_folium(m, width='stretch', height=600, returned_objects=["bounds"])
            
            # Store current map bounds in session state
            if map_data and map_data.get("bounds"):
                bounds = map_data["bounds"]
                if bounds:
                    south_west = bounds.get("_southWest", {})
                    north_east = bounds.get("_northEast", {})
                    
                    if south_west and north_east:
                        min_lon = south_west.get("lng")
                        min_lat = south_west.get("lat")
                        max_lon = north_east.get("lng")
                        max_lat = north_east.get("lat")
                        
                        if all(x is not None for x in [min_lon, min_lat, max_lon, max_lat]):
                            st.session_state.current_bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
        else:
            st.warning("No valid coordinates found in GeoJSON data.")
    else:
        st.info("No POIs found matching the criteria.")
else:
    st.error("⚠️ Failed to load GeoJSON data from API. Please check:")
    st.markdown("""
    - API server is running
    - Database connection is healthy
    - GeoJSON endpoint `/pois/geojson` is accessible
    """)