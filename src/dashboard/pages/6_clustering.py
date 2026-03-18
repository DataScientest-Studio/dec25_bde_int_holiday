"""
Airport Clustering Dashboard (France) - KMeans (k=5) + mapped nearest airport
"""
import os

import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="KMeans Airport Clustering", layout="wide")
st.title("✈️ POI KMeans Clustering (France) — k=5 and map each cluster to nearest airport")

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


def fix_mojibake(s):
    """
    Best-effort fix for strings like 'PhilomÃ¨ne' -> 'Philomène'
    (display only; doesn't modify DB).
    """
    if not isinstance(s, str):
        return s
    try:
        return s.encode("latin1").decode("utf-8")
    except Exception:
        return s


# session state to keep map stable across reruns
if "kmeans_payload" not in st.session_state:
    st.session_state.kmeans_payload = None


with st.sidebar:
    st.header("Settings")
    limit = st.slider("POIs to load (fit)", 100, 20000, 5000, 100)
    k = st.slider("k clusters", 2, 10, 5, 1)

    st.divider()
    st.header("POI display")
    max_pois_table = st.slider("Max POIs shown in table (per cluster)", 50, 5000, 500, 50)

    st.divider()
    st.header("Map options")
    show_pois_on_map = st.checkbox("Show POIs on map", value=True)
    poi_radius = st.slider("POI marker size", 2, 10, 6, 1)
    max_pois_draw = st.slider("Max POIs drawn per cluster (performance)", 100, 5000, 1500, 100)


tab1, tab2 = st.tabs(["KMeans Cluster Analysis", "Predict cluster & airport"])


with tab1:
    st.header("KMeans Cluster Analysis")

    colA, colB = st.columns([1, 2])
    with colA:
        if st.button("🔄 Run KMeans fit"):
            resp = requests.get(
                f"{API_URL}/api/kmeans-airport/fit",
                params={"limit": int(limit), "k": int(k)},
                timeout=180,
            )
            if resp.status_code != 200:
                show_http_error(resp, "KMeans fit error")
            else:
                st.session_state.kmeans_payload = resp.json()

        if st.button("🧹 Clear results"):
            st.session_state.kmeans_payload = None

    payload = st.session_state.kmeans_payload
    if not payload:
        st.info("Click **Run KMeans fit** to load clusters.")
        st.stop()

    clusters = payload.get("clusters", {}) or {}

    # Metrics (KMeans)
    m1, m2, m3 = st.columns(3)
    m1.metric("k clusters", int(payload.get("k", 0)))
    m2.metric("POIs input", int(payload.get("pois_input", 0)))
    m3.metric("POIs used", int(payload.get("pois_used", 0)))

    # Cluster summary table
    rows = []
    for cid, c in clusters.items():
        cid_int = int(cid)
        mapped = c.get("mapped_airport", {}) or {}
        rows.append(
            {
                "Cluster": cid_int,
                "POIs": int(c.get("size", 0) or 0),
                "Center lat": float(c.get("center_lat", 0.0) or 0.0),
                "Center lon": float(c.get("center_lon", 0.0) or 0.0),
                "Mapped airport IATA": mapped.get("iata"),
                "Mapped airport city": mapped.get("city"),
                "Center→airport (km)": float(mapped.get("cluster_center_to_airport_km", 0.0) or 0.0),
            }
        )

    df = pd.DataFrame(rows).sort_values(["POIs", "Cluster"], ascending=[False, True])
    st.subheader("Clusters")
    st.dataframe(df, use_container_width=True)

    # Choose cluster to visualize
    cluster_options = ["(All)"] + [int(x) for x in sorted(clusters.keys(), key=lambda s: int(s))]
    selected = st.selectbox("Show on map", cluster_options, index=0)

    # ---- NEW: POI table for selected cluster ----
    st.subheader("POIs in a cluster (table)")

    if selected == "(All)":
        st.info("Select a specific cluster in **Show on map** to list its POIs.")
    else:
        selected_cluster = clusters.get(str(selected), {}) or {}
        pois = selected_cluster.get("pois", []) or []

        if not pois:
            st.info("No POIs found in this cluster.")
        else:
            poi_df = pd.DataFrame(pois)

            # Fix encoding issues for display only
            if "label" in poi_df.columns:
                poi_df["label"] = poi_df["label"].apply(fix_mojibake)
            if "name" in poi_df.columns:
                poi_df["name"] = poi_df["name"].apply(fix_mojibake)

            preferred_cols = ["id", "label", "name", "type", "latitude", "longitude"]
            cols = [c for c in preferred_cols if c in poi_df.columns] + [c for c in poi_df.columns if c not in preferred_cols]

            st.caption(f"Showing up to {int(max_pois_table)} POIs for cluster {selected}.")
            st.dataframe(poi_df[cols].head(int(max_pois_table)), use_container_width=True)

            st.download_button(
                label=f"Download cluster {selected} POIs (CSV)",
                data=poi_df[cols].to_csv(index=False).encode("utf-8"),
                file_name=f"kmeans_cluster_{selected}_pois.csv",
                mime="text/csv",
            )

    # Map center: use selected cluster center, else mean of all centers
    if selected != "(All)":
        c = clusters[str(selected)]
        m = folium.Map(location=[c["center_lat"], c["center_lon"]], zoom_start=8)
    else:
        if len(df) > 0:
            m = folium.Map(location=[df["Center lat"].mean(), df["Center lon"].mean()], zoom_start=6)
        else:
            m = folium.Map(location=[46.2, 2.2], zoom_start=6)

    colors = ["red", "blue", "green", "purple", "orange", "darkred", "darkblue", "cadetblue", "darkgreen", "gray"]

    # Draw clusters
    for cid_str, cluster in sorted(clusters.items(), key=lambda kv: int(kv[0])):
        cid_int = int(cid_str)
        if selected != "(All)" and cid_int != selected:
            continue

        color = colors[cid_int % len(colors)]
        mapped = cluster.get("mapped_airport", {}) or {}

        # Cluster center marker
        folium.Marker(
            location=[cluster["center_lat"], cluster["center_lon"]],
            popup=f"Cluster {cid_int} (size={cluster.get('size', 0)})",
            icon=folium.Icon(color=color, icon="info-sign"),
        ).add_to(m)

        # Mapped airport marker
        if mapped.get("lat") is not None and mapped.get("lon") is not None:
            folium.Marker(
                location=[mapped["lat"], mapped["lon"]],
                popup=(
                    f"Mapped airport: {mapped.get('iata')} - {fix_mojibake(mapped.get('name'))} "
                    f"({fix_mojibake(mapped.get('city'))})<br>"
                    f"Center→airport: {float(mapped.get('cluster_center_to_airport_km', 0.0)):.1f} km"
                ),
                icon=folium.Icon(color="black", icon="plane", prefix="fa"),
            ).add_to(m)

        # POIs (limit for performance)
        if show_pois_on_map:
            for poi in (cluster.get("pois", []) or [])[: int(max_pois_draw)]:
                latv = poi.get("latitude")
                lonv = poi.get("longitude")
                if latv is None or lonv is None:
                    continue

                label = fix_mojibake(poi.get("label"))
                poi_type = poi.get("type")

                folium.CircleMarker(
                    location=[latv, lonv],
                    radius=int(poi_radius),
                    popup=f"{label}<br>Type: {poi_type}",
                    color=color,
                    fill=True,
                    fill_opacity=0.85,
                ).add_to(m)

    st.subheader("Map")
    st_folium(m, width=1200, height=650)


with tab2:
    st.header("Predict cluster & mapped airport (KMeans)")

    c1, c2 = st.columns(2)
    with c1:
        lat = st.number_input("Latitude", value=48.8566, format="%.6f")
    with c2:
        lon = st.number_input("Longitude", value=2.3522, format="%.6f")

    if st.button("✈️ Predict (KMeans)"):
        resp = requests.get(
            f"{API_URL}/api/kmeans-airport/predict",
            params={"lat": float(lat), "lon": float(lon), "limit": int(limit), "k": int(k)},
            timeout=60,
        )
        if resp.status_code != 200:
            show_http_error(resp, "Prediction error")
            st.stop()

        pred = resp.json().get("prediction", {}) or {}
        mapped = pred.get("mapped_airport", {}) or {}

        st.success(
            f"Cluster {pred.get('kmeans_cluster')} → "
            f"{mapped.get('iata')} - {fix_mojibake(mapped.get('name'))} ({fix_mojibake(mapped.get('city'))})"
        )
        st.write(f"Cluster center → airport: **{float(pred.get('cluster_center_to_airport_km', 0.0)):.1f} km**")