#!/usr/bin/env python3
"""
Find dense urban station clusters from Synoptic/MesoWest metadata.

Requires a Synoptic token, see https://synopticdata.com/
"""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple

import requests


SYNOPTIC_METADATA_URL = "https://api.synopticdata.com/v2/stations/metadata"


@dataclass(frozen=True)
class Station:
    stid: str
    name: str
    lat: float
    lon: float


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(a))


def latlon_to_xy_km(lat: float, lon: float, lat0: float, lon0: float) -> Tuple[float, float]:
    km_per_deg_lat = 110.574
    km_per_deg_lon = 111.320 * math.cos(math.radians(lat0))
    x = (lon - lon0) * km_per_deg_lon
    y = (lat - lat0) * km_per_deg_lat
    return x, y


def convex_hull(points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    if len(points) <= 1:
        return points
    points = sorted(points)

    def cross(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: List[Tuple[float, float]] = []
    for p in points:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper: List[Tuple[float, float]] = []
    for p in reversed(points):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


def polygon_area_km2(points: List[Tuple[float, float]]) -> Optional[float]:
    if len(points) < 3:
        return None
    area = 0.0
    for i in range(len(points)):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % len(points)]
        area += x1 * y2 - x2 * y1
    return abs(area) * 0.5


def fetch_metadata(
    token: str,
    lat: float,
    lon: float,
    radius_km: float,
    include_restricted: bool,
    timeout: int = 30,
) -> List[Station]:
    params = {
        "token": token,
        "radius": f"{lat},{lon},{radius_km}",
        "vars": "wind_speed,wind_direction",
        "status": "active",
    }
    response = requests.get(SYNOPTIC_METADATA_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    stations = []
    for raw in payload.get("STATION", []):
        if not include_restricted and raw.get("RESTRICTED"):
            continue
        try:
            stations.append(
                Station(
                    stid=str(raw.get("STID", "")).strip(),
                    name=str(raw.get("NAME", "")).strip(),
                    lat=float(raw.get("LATITUDE")),
                    lon=float(raw.get("LONGITUDE")),
                )
            )
        except (TypeError, ValueError):
            continue
    return stations


def pairwise_distances_km(stations: List[Station]) -> List[float]:
    distances = []
    for i, s in enumerate(stations):
        for j in range(i + 1, len(stations)):
            t = stations[j]
            distances.append(haversine_km(s.lat, s.lon, t.lat, t.lon))
    return distances


def find_dense_clusters(
    stations: Iterable[Station],
    min_distance_m: float,
    max_distance_m: float,
    min_stations: int,
) -> List[List[Station]]:
    stations = list(stations)
    min_distance_km = min_distance_m / 1000.0
    max_distance_km = max_distance_m / 1000.0
    clusters = []
    seen = set()
    for i, s in enumerate(stations):
        neighbors = [s]
        for j, t in enumerate(stations):
            if i == j:
                continue
            if haversine_km(s.lat, s.lon, t.lat, t.lon) <= max_distance_km:
                neighbors.append(t)
        if len(neighbors) >= min_stations:
            distances = pairwise_distances_km(neighbors)
            if distances and min(distances) < min_distance_km:
                continue
            key = tuple(sorted(st.stid for st in neighbors))
            if key not in seen:
                seen.add(key)
                clusters.append(neighbors)
    return clusters


def summarize_cluster(cluster: List[Station]) -> str:
    lat0 = sum(s.lat for s in cluster) / len(cluster)
    lon0 = sum(s.lon for s in cluster) / len(cluster)
    points = [latlon_to_xy_km(s.lat, s.lon, lat0, lon0) for s in cluster]
    hull = convex_hull(points)
    area = polygon_area_km2(hull)
    area_text = "n/a" if area is None else f"{area:.3f} km^2"
    return f"cluster size {len(cluster)}, hull area {area_text}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find dense station clusters from Synoptic metadata."
    )
    parser.add_argument("--lat", type=float, required=True, help="Center latitude")
    parser.add_argument("--lon", type=float, required=True, help="Center longitude")
    parser.add_argument("--radius-km", type=float, default=5.0, help="Search radius in km")
    parser.add_argument("--min-distance-m", type=float, default=50.0)
    parser.add_argument("--max-distance-m", type=float, default=200.0)
    parser.add_argument("--min-stations", type=int, default=3)
    parser.add_argument("--token", help="Synoptic token or set SYNOPTIC_TOKEN")
    parser.add_argument(
        "--allow-restricted",
        action="store_true",
        help="Include restricted stations (may lack data access)",
    )
    args = parser.parse_args()

    token = args.token or os.environ.get("SYNOPTIC_TOKEN")
    if not token:
        raise SystemExit("Provide --token or set SYNOPTIC_TOKEN")

    stations = fetch_metadata(
        token, args.lat, args.lon, args.radius_km, include_restricted=args.allow_restricted
    )
    if not stations:
        raise SystemExit("No stations found in radius, adjust --radius-km")

    clusters = find_dense_clusters(
        stations, args.min_distance_m, args.max_distance_m, args.min_stations
    )
    if not clusters:
        raise SystemExit("No clusters found, increase radius or distance threshold")

    for idx, cluster in enumerate(clusters[:5], start=1):
        print(f"Cluster {idx}: {summarize_cluster(cluster)}")
        for station in cluster:
            print(f"  {station.stid:6s} {station.lat:.5f}, {station.lon:.5f} {station.name}")


if __name__ == "__main__":
    main()

