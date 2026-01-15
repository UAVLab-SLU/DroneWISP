#!/usr/bin/env python3
"""
Find a small cluster of nearby urban ASOS stations using the IEM geojson catalog.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import csv
from pathlib import Path

import requests


IEM_ASOS_GEOJSON = "https://mesonet.agron.iastate.edu/geojson/network/ASOS.geojson"
DEFAULT_CATALOG = Path(__file__).with_name("station_catalog.csv")


CITY_CENTERS: Dict[str, Tuple[float, float]] = {
    "nyc": (40.7128, -74.0060),
    "chicago": (41.8781, -87.6298),
    "la": (34.0522, -118.2437),
    "boston": (42.3601, -71.0589),
    "dc": (38.9072, -77.0369),
    "houston": (29.7604, -95.3698),
    "seattle": (47.6062, -122.3321),
}


@dataclass
class Station:
    station_id: str
    name: str
    lat: float
    lon: float
    distance_km: float


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


def fetch_asos_geojson(timeout: int = 30) -> dict:
    response = requests.get(IEM_ASOS_GEOJSON, timeout=timeout)
    response.raise_for_status()
    return response.json()


def iter_geojson_stations(geojson: dict) -> Iterable[Tuple[str, str, float, float]]:
    for feature in geojson.get("features", []):
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or []
        if len(coords) < 2:
            continue
        lon, lat = coords[0], coords[1]
        props = feature.get("properties") or {}
        station_id = props.get("id") or props.get("sid") or ""
        name = props.get("sname") or props.get("name") or ""
        if not station_id or lat is None or lon is None:
            continue
        yield station_id, name, float(lat), float(lon)


def iter_catalog_stations(path: Path) -> Iterable[Tuple[str, str, float, float]]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            station_id = (row.get("station_id") or "").strip()
            name = (row.get("name") or "").strip()
            lat = row.get("lat")
            lon = row.get("lon")
            if not station_id or lat is None or lon is None:
                continue
            yield station_id, name, float(lat), float(lon)


def build_cluster(
    lat0: float,
    lon0: float,
    stations: Iterable[Tuple[str, str, float, float]],
    radius_km: float,
    max_stations: int,
) -> List[Station]:
    selected: List[Station] = []
    for station_id, name, lat, lon in stations:
        dist = haversine_km(lat0, lon0, lat, lon)
        if dist <= radius_km:
            selected.append(Station(station_id, name, lat, lon, dist))
    selected.sort(key=lambda s: s.distance_km)
    return selected[:max_stations]


def print_cluster_summary(
    cluster: List[Station], lat0: float, lon0: float, radius_km: float
) -> None:
    print(f"Stations within {radius_km:.1f} km of center:")
    for station in cluster:
        print(
            f"  {station.station_id:5s}  {station.distance_km:6.1f} km  "
            f"{station.lat:.4f}, {station.lon:.4f}  {station.name}"
        )

    if len(cluster) >= 3:
        points = [latlon_to_xy_km(s.lat, s.lon, lat0, lon0) for s in cluster]
        hull = convex_hull(points)
        area = polygon_area_km2(hull)
        if area is not None:
            print(f"Convex hull area: {area:.1f} km^2")
    else:
        print("Convex hull area: not enough stations for a polygon")


def resolve_center(args: argparse.Namespace) -> Tuple[float, float, str]:
    if args.lat is not None and args.lon is not None:
        return args.lat, args.lon, "custom"
    if args.city:
        key = args.city.strip().lower()
        if key not in CITY_CENTERS:
            raise SystemExit(f"Unknown city '{args.city}'. Available: {', '.join(CITY_CENTERS)}")
        lat0, lon0 = CITY_CENTERS[key]
        return lat0, lon0, key
    raise SystemExit("Provide --city or both --lat and --lon.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find nearby ASOS stations for an urban simulation domain."
    )
    parser.add_argument("--city", help="City key, e.g. nyc, chicago, la")
    parser.add_argument("--lat", type=float, help="Center latitude")
    parser.add_argument("--lon", type=float, help="Center longitude")
    parser.add_argument("--radius-km", type=float, default=40.0, help="Search radius in km")
    parser.add_argument("--max-stations", type=int, default=6, help="Max stations to list")
    parser.add_argument(
        "--catalog",
        type=Path,
        help="Optional CSV catalog path with station_id,name,lat,lon",
    )
    args = parser.parse_args()

    lat0, lon0, label = resolve_center(args)
    print(f"Center: {label} ({lat0:.4f}, {lon0:.4f})")

    stations: Iterable[Tuple[str, str, float, float]]
    catalog_path = args.catalog or DEFAULT_CATALOG
    try:
        geojson = fetch_asos_geojson()
        if geojson.get("features"):
            stations = iter_geojson_stations(geojson)
        else:
            stations = iter_catalog_stations(catalog_path)
            print(f"Catalog fallback: {catalog_path}")
    except requests.RequestException:
        stations = iter_catalog_stations(catalog_path)
        print(f"Catalog fallback: {catalog_path}")

    cluster = build_cluster(
        lat0=lat0,
        lon0=lon0,
        stations=stations,
        radius_km=args.radius_km,
        max_stations=args.max_stations,
    )

    if not cluster:
        raise SystemExit("No stations found in radius, increase --radius-km.")

    print_cluster_summary(cluster, lat0, lon0, args.radius_km)


if __name__ == "__main__":
    main()

