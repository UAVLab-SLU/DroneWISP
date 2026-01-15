#!/usr/bin/env python3
"""
Plot station locations on a static OpenStreetMap image.
"""

from __future__ import annotations

import argparse
from io import BytesIO
import math
from pathlib import Path
from typing import List, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import requests
from PIL import Image


TILE_URL = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"


def load_station_points(csv_path: Path) -> List[Tuple[str, float, float]]:
    df = pd.read_csv(csv_path)
    required = {"stid", "lat", "lon"}
    if not required.issubset(df.columns):
        raise SystemExit(f"CSV must contain columns: {sorted(required)}")
    points = []
    for stid, lat, lon in df[["stid", "lat", "lon"]].drop_duplicates().itertuples(index=False):
        points.append((str(stid), float(lat), float(lon)))
    if not points:
        raise SystemExit("No station points found in CSV")
    return points


def load_station_vectors(
    csv_path: Path, timestamp: str
) -> List[Tuple[str, float, float, float, float]]:
    df = pd.read_csv(csv_path)
    required = {"stid", "lat", "lon", "date_time", "wind_speed", "wind_direction"}
    if not required.issubset(df.columns):
        raise SystemExit(f"CSV must contain columns: {sorted(required)}")
    df_ts = df[df["date_time"] == timestamp]
    if df_ts.empty:
        raise SystemExit(f"No rows found for timestamp {timestamp}")
    vectors = []
    for row in df_ts.itertuples(index=False):
        vectors.append(
            (
                str(row.stid),
                float(row.lat),
                float(row.lon),
                float(row.wind_speed),
                float(row.wind_direction),
            )
        )
    return vectors


def bearing_to_uv(speed: float, direction_deg: float) -> Tuple[float, float]:
    theta = math.radians(direction_deg)
    u = speed * math.sin(theta)
    v = speed * math.cos(theta)
    return u, v


def latlon_to_tile(lat: float, lon: float, zoom: int) -> Tuple[int, int]:
    lat_rad = math.radians(lat)
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return x, y


def tile_to_latlon(x: int, y: int, zoom: int) -> Tuple[float, float]:
    n = 2 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon


def fetch_tile(
    z: int, x: int, y: int, tile_url: str, timeout: int = 30
) -> Image.Image:
    url = tile_url.format(z=z, x=x, y=y)
    headers = {"User-Agent": "DroneWISP/plot_station_map"}
    response = requests.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return Image.open(BytesIO(response.content)).convert("RGB")


def build_map_image(
    points: List[Tuple[str, float, float]],
    zoom: int,
    tile_url: str,
    timeout: int = 30,
) -> Tuple[Image.Image, Tuple[float, float, float, float]]:
    lats = [p[1] for p in points]
    lons = [p[2] for p in points]
    padding = 0.001
    lat_min, lat_max = min(lats) - padding, max(lats) + padding
    lon_min, lon_max = min(lons) - padding, max(lons) + padding

    x_min, y_max = latlon_to_tile(lat_min, lon_min, zoom)
    x_max, y_min = latlon_to_tile(lat_max, lon_max, zoom)

    x_min, x_max = min(x_min, x_max), max(x_min, x_max)
    y_min, y_max = min(y_min, y_max), max(y_min, y_max)

    tiles = []
    for y in range(y_min, y_max + 1):
        row = []
        for x in range(x_min, x_max + 1):
            row.append(fetch_tile(zoom, x, y, tile_url, timeout=timeout))
        tiles.append(row)

    tile_w, tile_h = tiles[0][0].size
    map_w = tile_w * len(tiles[0])
    map_h = tile_h * len(tiles)
    image = Image.new("RGB", (map_w, map_h))
    for row_idx, row in enumerate(tiles):
        for col_idx, tile in enumerate(row):
            image.paste(tile, (col_idx * tile_w, row_idx * tile_h))

    north_lat, west_lon = tile_to_latlon(x_min, y_min, zoom)
    south_lat, east_lon = tile_to_latlon(x_max + 1, y_max + 1, zoom)
    extent = (west_lon, east_lon, south_lat, north_lat)
    return image, extent


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot station points on a map.")
    parser.add_argument("--csv", required=True, type=Path, help="Input CSV with stid,lat,lon")
    parser.add_argument("--out", required=True, type=Path, help="Output PNG path")
    parser.add_argument("--zoom", type=int, default=16, help="Map zoom level")
    parser.add_argument(
        "--tile-url",
        default=TILE_URL,
        help="Tile URL template with {z}/{x}/{y}",
    )
    parser.add_argument("--timestamp", help="Optional timestamp to plot wind vectors")
    args = parser.parse_args()

    points = load_station_points(args.csv)
    map_image, extent = build_map_image(points, args.zoom, args.tile_url)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(map_image, extent=extent)
    lats = [p[1] for p in points]
    lons = [p[2] for p in points]
    ax.scatter(lons, lats, c="red", s=60, edgecolors="white", linewidths=0.8, zorder=3)
    for stid, lat, lon in points:
        ax.text(lon, lat, stid, fontsize=9, ha="left", va="bottom", color="black")
    if args.timestamp:
        vectors = load_station_vectors(args.csv, args.timestamp)
        for _, lat, lon, speed, direction in vectors:
            u, v = bearing_to_uv(speed, direction)
            ax.quiver(
                lon,
                lat,
                u,
                v,
                angles="xy",
                scale_units="xy",
                scale=0.8,
                color="blue",
                zorder=4,
            )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Station Locations")
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    fig.tight_layout()
    fig.savefig(args.out, dpi=150)
    plt.close(fig)
    print(f"Saved map to {args.out}")


if __name__ == "__main__":
    main()

