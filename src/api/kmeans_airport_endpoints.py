from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.db import get_db
from src.ml.kmeans_airport_clusterer import KMeansAirportClusterer
from src.ml.utils import get_pois_for_clustering

router = APIRouter(prefix="/api/kmeans-airport", tags=["kmeans-airport"])


@router.get("/fit")
def fit_kmeans_airport(
    limit: int = Query(5000, ge=1, le=50000),
    k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    pois = get_pois_for_clustering(db, limit=limit)
    model = KMeansAirportClusterer(k=k)
    result = model.fit(pois)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result)

    return result


@router.get("/predict")
def predict_kmeans_airport(
    lat: float = Query(..., ge=-90.0, le=90.0),
    lon: float = Query(..., ge=-180.0, le=180.0),
    limit: int = Query(5000, ge=1, le=50000, description="POIs used to fit before predicting"),
    k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    # Stateless demo: fit on the fly, then predict
    pois = get_pois_for_clustering(db, limit=limit)
    model = KMeansAirportClusterer(k=k)
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
        "fit_info": {"k": k, "pois_used": fit_result.get("pois_used")},
    }