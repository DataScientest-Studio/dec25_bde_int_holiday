from __future__ import annotations

import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.title("KMeans Elbow + Clusters")

limit = st.sidebar.number_input("POIs limit", min_value=1, max_value=50000, value=5000, step=500)
k_min = st.sidebar.number_input("k_min (auto)", min_value=1, max_value=20, value=2, step=1)
k_max = st.sidebar.number_input("k_max (auto)", min_value=1, max_value=20, value=12, step=1)
sample_size = st.sidebar.number_input("sample_size (auto)", min_value=100, max_value=50000, value=2000, step=100)

params = {"limit": int(limit), "k": "auto", "k_min": int(k_min), "k_max": int(k_max), "sample_size": int(sample_size)}

with st.spinner("Calling API..."):
    r = requests.get(f"{API_URL}/api/kmeans-airport/fit", params=params, timeout=120)
    st.caption(f"GET {r.url}")
    r.raise_for_status()
    data = r.json()

meta = data.get("_meta") or {}
elbow = meta.get("elbow") or {}

st.subheader("Meta")
st.json(
    {
        "k_requested": meta.get("k_requested"),
        "k_resolved": meta.get("k_resolved"),
        "elbow_ok": elbow.get("ok"),
        "pois_input": elbow.get("pois_input"),
        "pois_used": elbow.get("pois_used"),
        "sampled_points": elbow.get("sampled_points"),
    }
)

# ---- elbow chart ----
k_values = elbow.get("k_values") or []
inertias = elbow.get("inertias") or []

st.subheader("Elbow (inertia vs k)")
if len(k_values) >= 2 and len(inertias) == len(k_values):
    chart_df = pd.DataFrame({"k": k_values, "inertia": inertias}).set_index("k")
    st.line_chart(chart_df)
else:
    st.warning("No elbow data returned (or not enough points).")
    st.json(elbow)

# ---- clusters ----
clusters = data.get("clusters") or {}

st.subheader("Clusters")
st.write(f"Clusters returned: {len(clusters)}")

if not clusters:
    st.warning("No clusters in response. Showing full response:")
    st.json(data)
else:
    # build a small summary table
    rows = []
    for key, c in clusters.items():
        mapped = (c.get("mapped_airport") or {})
        rows.append(
            {
                "cluster": int(c.get("kmeans_cluster", key)),
                "size": c.get("size"),
                "center_lat": c.get("center_lat"),
                "center_lon": c.get("center_lon"),
                "airport_iata": mapped.get("iata"),
                "airport_city": mapped.get("city"),
                "airport_name": mapped.get("name"),
                "center_to_airport_km": mapped.get("cluster_center_to_airport_km"),
            }
        )

    df = pd.DataFrame(rows).sort_values("cluster")
    st.dataframe(df, use_container_width=True)

    # Optional: map cluster centers
    st.subheader("Cluster centers map")
    map_df = df.rename(columns={"center_lat": "lat", "center_lon": "lon"})[["lat", "lon"]].dropna()
    if not map_df.empty:
        st.map(map_df)