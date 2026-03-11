#!/usr/bin/env python3
"""
Compute and plot a bounding box defined by station constraints.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.ticker import ScalarFormatter
import pandas as pd

from plot_station_map import TILE_URL, build_map_image, load_station_points


METERS_PER_DEG_LAT = 111_320.0


def meters_to_deg_lat(meters: float) -> float:
    return meters / METERS_PER_DEG_LAT


def meters_to_deg_lon(meters: float, lat: float) -> float:
    return meters / (METERS_PER_DEG_LAT * math.cos(math.radians(lat)))


def compute_bbox(
    lat_north: float,
    lon_center: float,
    lat_south_reference: float,
    south_offset_m: float,
    ratio_long_to_lat: float,
) -> tuple[float, float, float, float]:
    lat_south = lat_south_reference - meters_to_deg_lat(south_offset_m)
    height_deg = lat_north - lat_south
    height_m = height_deg * METERS_PER_DEG_LAT
    width_m = height_m * ratio_long_to_lat
    lat_mid = (lat_north + lat_south) / 2.0
    width_deg = meters_to_deg_lon(width_m, lat_mid)
    lon_west = lon_center - width_deg / 2.0
    lon_east = lon_center + width_deg / 2.0
    return lat_south, lat_north, lon_west, lon_east


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot a bounding box on a map.")
    parser.add_argument("--csv", required=True, type=Path, help="Input CSV with stid,lat,lon")
    parser.add_argument("--north-stid", required=True, help="Station on north boundary")
    parser.add_argument("--south-stid", required=True, help="Station near south boundary")
    parser.add_argument("--south-offset-m", type=float, default=50.0)
    parser.add_argument(
        "--ratio-long-lat",
        default="1:2",
        help="Ratio long:lat, e.g. 1:2 means width is half height",
    )
    parser.add_argument("--zoom", type=int, default=17)
    parser.add_argument(
        "--tile-url",
        default=TILE_URL,
        help="Tile URL template with {z}/{x}/{y}",
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--timestamp",
        default="2026-01-09T17:30:00Z",
        help="Timestamp for wind vectors, format YYYY-MM-DDTHH:MM:SSZ",
    )
    args = parser.parse_args()

    ratio_parts = args.ratio_long_lat.split(":")
    if len(ratio_parts) != 2:
        raise SystemExit("ratio-long-lat must be in A:B format")
    ratio_long_to_lat = float(ratio_parts[0]) / float(ratio_parts[1])

    df = pd.read_csv(args.csv)
    north_row = df[df["stid"] == args.north_stid].iloc[0]
    south_row = df[df["stid"] == args.south_stid].iloc[0]

    lat_north = float(north_row["lat"])
    lon_center = (float(north_row["lon"]) + float(south_row["lon"])) / 2.0
    lat_south_ref = float(south_row["lat"])

    lat_south, lat_north, lon_west, lon_east = compute_bbox(
        lat_north=lat_north,
        lon_center=lon_center,
        lat_south_reference=lat_south_ref,
        south_offset_m=args.south_offset_m,
        ratio_long_to_lat=ratio_long_to_lat,
    )

    print("bbox_lat_south", lat_south)
    print("bbox_lat_north", lat_north)
    print("bbox_lon_west", lon_west)
    print("bbox_lon_east", lon_east)

    points = load_station_points(args.csv)
    # Build tiles using the bbox corners so the map extent is in absolute lat/lon
    bbox_points = [
        ("bbox_sw", lat_south, lon_west),
        ("bbox_ne", lat_north, lon_east),
    ]
    map_image, extent = build_map_image(bbox_points, args.zoom, args.tile_url)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.imshow(map_image, extent=extent)
    lats = [p[1] for p in points]
    lons = [p[2] for p in points]
    ax.scatter(lons, lats, c="red", s=60, edgecolors="white", linewidths=0.8, zorder=3)
    for stid, lat, lon in points:
        ax.text(lon, lat, stid, fontsize=9, ha="left", va="bottom", color="black")

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Study Area Stations and Wind Vectors at {args.timestamp}")
    ax.xaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    ax.yaxis.set_major_formatter(ScalarFormatter(useOffset=False))
    ax.locator_params(axis="x", nbins=5)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    rect = Rectangle(
        (lon_west, lat_south),
        lon_east - lon_west,
        lat_north - lat_south,
        linewidth=2.0,
        edgecolor="magenta",
        facecolor="none",
        zorder=2,
    )
    ax.add_patch(rect)
    # Keep vector arrows at a constant 1 cm length in display space
    vector_stids = {"0512W", "0514W", "0516W"}
    df_ts = df[(df["date_time"] == args.timestamp) & (df["stid"].isin(vector_stids))]
    if not df_ts.empty:
        arrow_length_cm = 1.0
        length_px = arrow_length_cm / 2.54 * fig.dpi
        for _, row in df_ts.iterrows():
            speed = float(row["wind_speed"])
            direction = float(row["wind_direction"])
            u = -speed * math.sin(math.radians(direction))
            v = -speed * math.cos(math.radians(direction))

            x0 = float(row["lon"])
            y0 = float(row["lat"])
            p0 = ax.transData.transform((x0, y0))
            p_dir = ax.transData.transform((x0 + u, y0 + v))
            dpx = p_dir[0] - p0[0]
            dpy = p_dir[1] - p0[1]
            norm = math.hypot(dpx, dpy)
            if norm == 0:
                continue
            ux = dpx / norm
            uy = dpy / norm
            p1 = (p0[0] + ux * length_px, p0[1] + uy * length_px)
            x1, y1 = ax.transData.inverted().transform(p1)
            ax.quiver(
                x0,
                y0,
                x1 - x0,
                y1 - y0,
                angles="xy",
                scale_units="xy",
                scale=1.0,
                color="blue",
                zorder=4,
            )
    legend_elements = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="red", markersize=8, label="Stations"),
        Line2D([0], [0], color="blue", lw=2, marker=">", markersize=8, label="Wind vectors"),
        Line2D([0], [0], color="magenta", lw=2, label="Bounding box"),
    ]
    ax.legend(handles=legend_elements, loc="upper right")
    fig.tight_layout(pad=0.2)
    fig.savefig(args.out, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()

