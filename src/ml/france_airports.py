from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt


@dataclass(frozen=True)
class Airport:
    iata: str
    name: str
    city: str
    lat: float
    lon: float


FRANCE_AIRPORTS: tuple[Airport, ...] = (
    Airport("CDG", "Paris Charles de Gaulle", "Paris", 49.0097, 2.5479),
    Airport("ORY", "Paris Orly", "Paris", 48.7262, 2.3652),
    Airport("BVA", "Paris Beauvais", "Beauvais", 49.4544, 2.1128),
    Airport("LYS", "Lyon–Saint-Exupéry", "Lyon", 45.7256, 5.0811),
    Airport("MRS", "Marseille Provence", "Marseille", 43.4393, 5.2214),
    Airport("NCE", "Nice Côte d'Azur", "Nice", 43.6653, 7.2150),
    Airport("TLS", "Toulouse–Blagnac", "Toulouse", 43.6293, 1.3638),
    Airport("BOD", "Bordeaux–Mérignac", "Bordeaux", 44.8283, -0.7156),
    Airport("NTE", "Nantes Atlantique", "Nantes", 47.1532, -1.6107),
    Airport("LIL", "Lille", "Lille", 50.5636, 3.0869),
    Airport("SXB", "Strasbourg", "Strasbourg", 48.5383, 7.6282),
    Airport("MPL", "Montpellier Méditerranée", "Montpellier", 43.5762, 3.9630),
    Airport("BIQ", "Biarritz", "Biarritz", 43.4684, -1.5311),
)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0088
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    return 2 * r * atan2(sqrt(a), sqrt(1 - a))