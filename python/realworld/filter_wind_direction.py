#!/usr/bin/env python3
"""
Filter wind observations by direction sectors.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def direction_mask(series: pd.Series, sector: str) -> pd.Series:
    sector = sector.lower()
    if sector == "north":
        return (series >= 337.5) | (series < 22.5)
    if sector == "northeast":
        return (series >= 22.5) & (series < 67.5)
    if sector == "northwest":
        return (series >= 292.5) & (series < 337.5)
    raise SystemExit(f"Unknown sector '{sector}'")


def main() -> None:
    parser = argparse.ArgumentParser(description="Filter wind data by direction.")
    parser.add_argument("--csv", required=True, type=Path, help="Input CSV file")
    parser.add_argument("--out", required=True, type=Path, help="Output CSV file")
    parser.add_argument(
        "--sectors",
        default="north,northeast,northwest",
        help="Comma-separated sectors: north,northeast,northwest",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.csv)
    if "wind_direction" not in df.columns:
        raise SystemExit("Input CSV must contain wind_direction column")

    wind_dir = pd.to_numeric(df["wind_direction"], errors="coerce")
    mask = pd.Series(False, index=df.index)
    for sector in [s.strip() for s in args.sectors.split(",") if s.strip()]:
        mask |= direction_mask(wind_dir, sector)

    filtered = df[mask & wind_dir.notna()]
    filtered.to_csv(args.out, index=False)
    print(f"Saved filtered rows: {len(filtered)} to {args.out}")


if __name__ == "__main__":
    main()

