from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.ml.auto_k_elbow import choose_k_elbow
from src.ml.kmeans_airport_clusterer import KMeansAirportClusterer
from src.ml.utils import get_pois_for_clustering

router = APIRouter(prefix="/api/kmeans-airport", tags=["kmeans-airport"])


def _resolve_k(k: str, pois, k_min: int, k_max: int, sample_size: int) -> tuple[int, dict | None]:
    k_raw = (k or "").strip().lower()

    if k_raw == "auto":
        elbow = choose_k_elbow(
            pois,
            k_min=k_min,
            k_max=k_max,
            sample_size=sample_size,
            enforce_france_bbox=True,
        )

        if elbow.get("ok") and elbow.get("suggested_k") is not None:
            return int(elbow["suggested_k"]), elbow

        # Fallback if elbow can't compute (too few POIs etc.)
        fallback_k = min(5, max(1, elbow.get("pois_used", 1)))
        return int(fallback_k), elbow

    try:
        k_int = int(k_raw)
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid k='{k}'. Use an integer or 'auto'.")

    if k_int < 1:
        raise HTTPException(status_code=400, detail="k must be >= 1")

    return k_int, None


@router.get("/fit")
def fit_kmeans_airport(
    limit: int = Query(5000, ge=1, le=50000),
    k: str = Query("auto", description="Number of clusters (int) or 'auto' (elbow method)"),
    k_min: int = Query(2, ge=1, le=20, description="Used only when k=auto"),
    k_max: int = Query(12, ge=1, le=20, description="Used only when k=auto"),
    sample_size: int = Query(2000, ge=100, le=50000, description="Used only when k=auto"),
    db: Session = Depends(get_db),
):
    pois = get_pois_for_clustering(db, limit=limit)
    model_k, elbow = _resolve_k(k, pois, k_min=k_min, k_max=k_max, sample_size=sample_size)

    model = KMeansAirportClusterer(k=model_k)
    result = model.fit(pois)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    # Backward compatible: return original result keys at top-level (clusters, k, etc.)
    payload = dict(result)
    payload["_meta"] = {
        "k_requested": k,
        "k_resolved": model_k,
        "elbow": elbow,  # None when k is numeric
    }
    return payload


@router.get("/predict")
def predict_kmeans_airport(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    limit: int = Query(5000, ge=1, le=50000, description="POIs used to fit before predicting"),
    k: str = Query("auto", description="Number of clusters (int) or 'auto' (elbow method)"),
    k_min: int = Query(2, ge=1, le=20, description="Used only when k=auto"),
    k_max: int = Query(12, ge=1, le=20, description="Used only when k=auto"),
    sample_size: int = Query(2000, ge=100, le=50000, description="Used only when k=auto"),
    db: Session = Depends(get_db),
):
    # Stateless demo: fit on the fly, then predict
    pois = get_pois_for_clustering(db, limit=limit)
    model_k, elbow = _resolve_k(k, pois, k_min=k_min, k_max=k_max, sample_size=sample_size)

    model = KMeansAirportClusterer(k=model_k)
    fit_result = model.fit(pois)

    if "error" in fit_result:
        raise HTTPException(status_code=400, detail=fit_result)

    pred = model.predict(float(lat), float(lon))
    if pred is None:
        raise HTTPException(status_code=404, detail="Model not fitted or coordinate outside France bbox")

    return {
        "input": {"lat": lat, "lon": lon},
        "prediction": {
            "kmeans_cluster": pred.kmeans_cluster,
            "cluster_center_lat": pred.cluster_center_lat,
            "cluster_center_lon": pred.cluster_center_lon,
            "mapped_airport": {
                "iata": pred.mapped_airport_iata,
                "name": pred.mapped_airport_name,
                "city": pred.mapped_airport_city,
                "lat": pred.mapped_airport_lat,
                "lon": pred.mapped_airport_lon,
            },
            "cluster_center_to_airport_km": pred.cluster_center_to_airport_km,
        },
        "fit_info": {"pois_used": fit_result.get("pois_used")},
        "_meta": {
            "k_requested": k,
            "k_resolved": model_k,
            "elbow": elbow,
        },
    }