from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
from sklearn.cluster import KMeans


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


def _knee_from_line(k_values: List[int], inertias: List[float]) -> Optional[int]:
    """
    Elbow approximation: point with max distance to line between endpoints.
    """
    if len(k_values) < 3:
        return None

    x = np.array(k_values, dtype=float)
    y = np.array(inertias, dtype=float)

    x1, y1 = x[0], y[0]
    x2, y2 = x[-1], y[-1]
    denom = np.hypot(x2 - x1, y2 - y1)
    if denom == 0:
        return None

    distances = np.abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / denom
    idx = int(np.argmax(distances[1:-1]) + 1)  # ignore endpoints
    return int(k_values[idx])


def choose_k_elbow(
    pois: List[Dict[str, Any]],
    k_min: int = 2,
    k_max: int = 12,
    random_state: int = 42,
    enforce_france_bbox: bool = True,
    sample_size: int = 2000,
    n_init: int = 10,
) -> Dict[str, Any]:
    coords: List[List[float]] = []
    for p in pois:
        lat = _safe_float(p.get("latitude"))
        lon = _safe_float(p.get("longitude"))
        if lat is None or lon is None:
            continue
        if enforce_france_bbox and not _looks_like_france(lat, lon):
            continue
        coords.append([lat, lon])

    pois_used = len(coords)
    if pois_used < k_min:
        return {
            "ok": False,
            "error": "Not enough POIs with valid coordinates to compute elbow",
            "pois_input": len(pois),
            "pois_used": pois_used,
            "k_values": [],
            "inertias": [],
            "suggested_k": None,
        }

    X = np.array(coords, dtype=float)

    # sample for speed (important when POIs is big)
    if X.shape[0] > sample_size:
        rng = np.random.default_rng(random_state)
        idx = rng.choice(X.shape[0], size=sample_size, replace=False)
        X = X[idx]

    k_values = list(range(k_min, min(k_max, X.shape[0]) + 1))
    inertias: List[float] = []
    for k in k_values:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=n_init)
        km.fit(X)
        inertias.append(float(km.inertia_))

    suggested_k = _knee_from_line(k_values, inertias)

    return {
        "ok": True,
        "pois_input": len(pois),
        "pois_used": pois_used,
        "sampled_points": int(X.shape[0]),
        "k_values": k_values,
        "inertias": inertias,
        "suggested_k": suggested_k,
    }