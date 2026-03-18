from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sklearn.cluster import KMeans

from src.ml.france_airports import FRANCE_AIRPORTS, Airport, haversine_km


def _safe_float(x: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if x is None:
            return default
        return float(x)
    except Exception:
        return default


def _looks_like_france(lat: float, lon: float) -> bool:
    # metropolitan France + Corsica rough bbox
    return (41.0 <= lat <= 51.6) and (-5.6 <= lon <= 10.3)


@dataclass(frozen=True)
class KMeansAirportPrediction:
    kmeans_cluster: int
    cluster_center_lat: float
    cluster_center_lon: float
    mapped_airport_iata: str
    mapped_airport_name: str
    mapped_airport_city: str
    mapped_airport_lat: float
    mapped_airport_lon: float
    cluster_center_to_airport_km: float


class KMeansAirportClusterer:
    """
    KMeans clustering (k clusters) over POI coordinates, then map each cluster to nearest airport.

    This is a 2-step model:
      1) ML: KMeans assigns points to 0..k-1
      2) Post-processing: each cluster center is mapped to the nearest airport
    """

    def __init__(
        self,
        k: int = 5,
        airports: Tuple[Airport, ...] = FRANCE_AIRPORTS,
        random_state: int = 42,
        enforce_france_bbox: bool = True,
    ):
        if k < 1:
            raise ValueError("k must be >= 1")

        self.k = int(k)
        self.airports = tuple(sorted(airports, key=lambda a: a.iata))
        self.random_state = int(random_state)
        self.enforce_france_bbox = bool(enforce_france_bbox)

        self.kmeans: Optional[KMeans] = None
        self.cluster_to_airport: Dict[int, Airport] = {}
        self.fitted: bool = False

    def _nearest_airport(self, lat: float, lon: float) -> Airport:
        return min(self.airports, key=lambda a: haversine_km(lat, lon, a.lat, a.lon))

    def fit(self, pois: List[Dict[str, Any]]) -> Dict[str, Any]:
        coords: List[List[float]] = []
        aligned: List[Dict[str, Any]] = []

        for p in pois:
            lat = _safe_float(p.get("latitude"))
            lon = _safe_float(p.get("longitude"))
            if lat is None or lon is None:
                continue
            if self.enforce_france_bbox and not _looks_like_france(lat, lon):
                continue

            coords.append([lat, lon])
            aligned.append(p)

        if len(coords) < self.k:
            return {
                "error": "Not enough POIs with valid France coordinates to fit KMeans",
                "k": self.k,
                "pois_input": len(pois),
                "pois_used": len(coords),
            }

        X = np.array(coords, dtype=float)

        self.kmeans = KMeans(n_clusters=self.k, random_state=self.random_state, n_init=10)
        labels = self.kmeans.fit_predict(X)
        centers = self.kmeans.cluster_centers_

        # map each cluster center -> nearest airport
        self.cluster_to_airport = {}
        for cluster_idx in range(self.k):
            c_lat = float(centers[cluster_idx][0])
            c_lon = float(centers[cluster_idx][1])
            self.cluster_to_airport[cluster_idx] = self._nearest_airport(c_lat, c_lon)

        self.fitted = True

        clusters: Dict[int, Dict[str, Any]] = {}
        for cluster_idx in range(self.k):
            c_lat = float(centers[cluster_idx][0])
            c_lon = float(centers[cluster_idx][1])
            airport = self.cluster_to_airport[cluster_idx]

            clusters[cluster_idx] = {
                "kmeans_cluster": cluster_idx,
                "center_lat": c_lat,
                "center_lon": c_lon,
                "mapped_airport": {
                    "iata": airport.iata,
                    "name": airport.name,
                    "city": airport.city,
                    "lat": airport.lat,
                    "lon": airport.lon,
                    "cluster_center_to_airport_km": float(haversine_km(c_lat, c_lon, airport.lat, airport.lon)),
                },
                "size": 0,
                "pois": [],
            }

        for p, lbl in zip(aligned, labels.tolist()):
            lbl = int(lbl)
            clusters[lbl]["size"] += 1
            clusters[lbl]["pois"].append(
                {
                    "id": p.get("id"),
                    "label": p.get("label") or p.get("name") or p.get("id") or "POI",
                    "name": p.get("name") or p.get("label") or p.get("id") or "POI",
                    "type": p.get("type", "unknown"),
                    "latitude": float(p["latitude"]),
                    "longitude": float(p["longitude"]),
                }
            )

        return {
            "model": "kmeans_k_then_map_cluster_to_nearest_airport",
            "k": self.k,
            "pois_input": len(pois),
            "pois_used": len(aligned),
            "clusters": clusters,
        }

    def predict(self, lat: float, lon: float) -> Optional[KMeansAirportPrediction]:
        if not self.kmeans or not self.fitted:
            return None
        if self.enforce_france_bbox and not _looks_like_france(lat, lon):
            return None

        lbl = int(self.kmeans.predict(np.array([[float(lat), float(lon)]], dtype=float))[0])
        center = self.kmeans.cluster_centers_[lbl]

        airport = self.cluster_to_airport[lbl]
        dist = float(haversine_km(float(center[0]), float(center[1]), airport.lat, airport.lon))

        return KMeansAirportPrediction(
            kmeans_cluster=lbl,
            cluster_center_lat=float(center[0]),
            cluster_center_lon=float(center[1]),
            mapped_airport_iata=airport.iata,
            mapped_airport_name=airport.name,
            mapped_airport_city=airport.city,
            mapped_airport_lat=airport.lat,
            mapped_airport_lon=airport.lon,
            cluster_center_to_airport_km=dist,
        )