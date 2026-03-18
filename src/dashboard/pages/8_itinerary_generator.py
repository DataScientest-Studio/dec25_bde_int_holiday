"""
Itinerary Generator (Greedy) - calls FastAPI /itinerary
"""
import os
import requests
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from streamlit.errors import StreamlitSecretNotFoundError

st.set_page_config(page_title="Itinerary Generator", layout="wide")
st.title("🗺️ Day-by-day Itinerary Generator (Greedy)")

DEFAULT_API_URL = "http://localhost:8000"
API_URL = os.getenv("API_BASE_URL")
if not API_URL:
    try:
        API_URL = st.secrets.get("API_BASE_URL", DEFAULT_API_URL)
    except StreamlitSecretNotFoundError:
        API_URL = DEFAULT_API_URL

st.caption(f"API_URL = {API_URL}")


def show_http_error(resp: requests.Response, prefix: str = "API error"):
    st.error(f"{prefix} {resp.status_code}: {resp.text}")


# Persist last result
if "itinerary_payload" not in st.session_state:
    st.session_state.itinerary_payload = None


with st.sidebar:
    st.header("Trip inputs")

    lat = st.number_input("Start latitude", value=48.8566, format="%.6f", min_value=-90.0, max_value=90.0)
    lon = st.number_input("Start longitude", value=2.3522, format="%.6f", min_value=-180.0, max_value=180.0)

    days = st.slider("Days", min_value=1, max_value=30, value=3, step=1)
    radius_km = st.slider("Search radius (km)", min_value=1, max_value=500, value=50, step=1)
    limit_per_day = st.slider("POIs per day", min_value=1, max_value=20, value=5, step=1)

    st.header("Preferences")
    types = st.text_input("POI types (comma-separated)", value="Museum,Restaurant")

    st.divider()
    st.header("Map")
    poi_radius = st.slider("Marker size", min_value=2, max_value=10, value=6, step=1)


st.subheader("Run itinerary generation")

col1, col2 = st.columns([1, 1])
with col1:
    if st.button("Generate itinerary"):
        params = {
            "lat": float(lat),
            "lon": float(lon),
            "days": int(days),
            "radius_km": float(radius_km),
            "limit_per_day": int(limit_per_day),
        }
        # Only send "types" if user provided something non-empty
        if types.strip():
            params["types"] = types.strip()

        resp = requests.get(f"{API_URL}/itinerary", params=params, timeout=180)
        if resp.status_code != 200:
            show_http_error(resp, "Itinerary error")
        else:
            st.session_state.itinerary_payload = resp.json()

with col2:
    if st.button("Clear"):
        st.session_state.itinerary_payload = None


payload = st.session_state.itinerary_payload
if not payload:
    st.info("Click **Generate itinerary** to run the algorithm.")
    st.stop()


# ---- Summary metrics ----
it_days = payload.get("itinerary", []) or []
total_found = int(payload.get("total_pois_found", 0) or 0)
total_selected = int(payload.get("total_pois_selected", 0) or 0)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Days returned", len(it_days))
m2.metric("POIs found", total_found)
m3.metric("POIs selected", total_selected)
m4.metric("POIs/day (limit)", int(payload.get("limit_per_day", 0) or 0))

st.write("**Start location:**", payload.get("start_location"))


# ---- Day-by-day tables ----
st.subheader("Day-by-day itinerary")

for day in it_days:
    day_num = day.get("day")
    pois = day.get("pois", []) or []
    df = pd.DataFrame(pois)

    with st.expander(f"Day {day_num} — {len(pois)} POIs", expanded=(day_num == 1)):
        if df.empty:
            st.write("No POIs selected for this day.")
        else:
            # Reorder columns if present
            preferred_cols = [
                "id", "label", "type", "city",
                "distance_from_previous_km",
                "latitude", "longitude", "uri",
            ]
            cols = [c for c in preferred_cols if c in df.columns] + [c for c in df.columns if c not in preferred_cols]
            st.dataframe(df[cols], use_container_width=True)


# ---- Map ----
st.subheader("Map view")

# Pick center for map: use start location
start = payload.get("start_location", {}) or {}
map_lat = float(start.get("latitude", lat))
map_lon = float(start.get("longitude", lon))

m = folium.Map(location=[map_lat, map_lon], zoom_start=10)

# Marker for start
folium.Marker(
    location=[map_lat, map_lon],
    popup="Start location",
    icon=folium.Icon(color="black", icon="home", prefix="fa"),
).add_to(m)

day_colors = ["red", "blue", "green", "purple", "orange", "darkred", "darkblue", "cadetblue", "darkgreen", "gray"]

for day in it_days:
    day_num = int(day.get("day", 1))
    color = day_colors[(day_num - 1) % len(day_colors)]
    pois = day.get("pois", []) or []

    # Polyline route (simple straight segments)
    coords = []
    for poi in pois:
        if poi.get("latitude") is None or poi.get("longitude") is None:
            continue
        coords.append([float(poi["latitude"]), float(poi["longitude"])])

        folium.CircleMarker(
            location=[float(poi["latitude"]), float(poi["longitude"])],
            radius=int(poi_radius),
            color=color,
            fill=True,
            fill_opacity=0.85,
            popup=(
                f"Day {day_num}<br>"
                f"{poi.get('label')}<br>"
                f"Type: {poi.get('type')}<br>"
                f"City: {poi.get('city')}<br>"
                f"Δ km: {poi.get('distance_from_previous_km')}"
            ),
        ).add_to(m)

    if len(coords) >= 2:
        folium.PolyLine(coords, color=color, weight=3, opacity=0.8).add_to(m)

st_folium(m, width=1200, height=650)