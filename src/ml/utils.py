"""
Utilities for geographic clustering and itinerary ML.
"""
from typing import List, Dict, Optional, Any
import numpy as np
from sqlalchemy.orm import Session
from src.api.models import POI
import logging

logger = logging.getLogger(__name__)


def get_pois_for_clustering(db: Session, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    query = db.query(POI).filter(
        POI.latitude.isnot(None),
        POI.longitude.isnot(None),
    )

    if limit:
        query = query.limit(limit)

    pois = query.all()

    out: List[Dict[str, Any]] = []
    for poi in pois:
        label = poi.label or poi.id

        try:
            lat = float(poi.latitude) if poi.latitude is not None else None
            lon = float(poi.longitude) if poi.longitude is not None else None
        except Exception:
            logger.warning("Invalid coordinates for POI id=%s", poi.id)
            continue

        if lat is None or lon is None:
            continue

        out.append(
            {
                "id": poi.id,
                "label": label,
                "name": label,
                "type": poi.type,
                "latitude": lat,
                "longitude": lon,
                "description": poi.description,
                "city": getattr(poi, "city", None),
                "department_code": getattr(poi, "department_code", None),
                "uri": getattr(poi, "uri", None),
            }
        )

    return out


def calculate_pairwise_distances(coords: np.ndarray) -> np.ndarray:
    from scipy.spatial.distance import cdist

    distances_degrees = cdist(coords, coords, metric="euclidean")
    return distances_degrees * 111.0


def calculate_activity_diversity(activity_types: List[str]) -> float:
    if not activity_types:
        return 0.0
    return len(set(activity_types)) / len(activity_types)