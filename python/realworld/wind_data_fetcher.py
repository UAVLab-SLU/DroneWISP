#!/usr/bin/env python3
"""
Fetch urban wind observations from Iowa State Mesonet ASOS archive and validate
temporal resolution for CFD comparison.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
from typing import Optional, Tuple

import pandas as pd
import requests


ASOS_URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"


@dataclass
class WindDataSummary:
    station: str
    rows: int
    missing_speed: int
    missing_dir: int
    median_minutes: Optional[float]
    max_gap_minutes: Optional[float]
    speed_unit: str


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _build_params(station: str, start: datetime, end: datetime) -> dict:
    return {
        "station": station,
        "data": "sknt,drct",
        "year1": start.year,
        "month1": start.month,
        "day1": start.day,
        "hour1": start.hour,
        "minute1": start.minute,
        "year2": end.year,
        "month2": end.month,
        "day2": end.day,
        "hour2": end.hour,
        "minute2": end.minute,
        "tz": "UTC",
        "format": "comma",
        "latlon": "yes",
        "missing": "empty",
        "direct": "yes",
    }


def _load_wind_dataframe(csv_text: str) -> pd.DataFrame:
    if "ERROR" in csv_text[:200].upper():
        raise RuntimeError(f"ASOS request returned error: {csv_text[:200]}")
    df = pd.read_csv(StringIO(csv_text), comment="#")
    if df.empty:
        raise RuntimeError("ASOS request returned no rows")
    if "valid" not in df.columns:
        raise RuntimeError(f"Missing 'valid' timestamp column, got {df.columns.tolist()}")
    return df


def _normalize_wind_columns(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series, str]:
    speed_col = None
    dir_col = None
    if "sknt" in df.columns:
        speed_col = "sknt"
        speed_unit = "knots"
    elif "wind_speed" in df.columns:
        speed_col = "wind_speed"
        speed_unit = "unknown"
    else:
        raise RuntimeError(f"No wind speed column found in {df.columns.tolist()}")

    if "drct" in df.columns:
        dir_col = "drct"
    elif "wind_dir" in df.columns:
        dir_col = "wind_dir"
    else:
        raise RuntimeError(f"No wind direction column found in {df.columns.tolist()}")

    return df[speed_col], df[dir_col], speed_unit


def _compute_resolution_minutes(df: pd.DataFrame) -> Tuple[Optional[float], Optional[float]]:
    times = pd.to_datetime(df["valid"], errors="coerce")
    times = times.dropna().sort_values()
    if len(times) < 2:
        return None, None
    deltas = times.diff().dropna().dt.total_seconds() / 60.0
    if deltas.empty:
        return None, None
    return float(deltas.median()), float(deltas.max())


def fetch_wind_data(
    station: str, start: datetime, end: datetime, timeout: int = 30
) -> pd.DataFrame:
    params = _build_params(station, start, end)
    response = requests.get(ASOS_URL, params=params, timeout=timeout)
    response.raise_for_status()
    return _load_wind_dataframe(response.text)


def validate_wind_data(df: pd.DataFrame, station: str) -> WindDataSummary:
    speed, direction, speed_unit = _normalize_wind_columns(df)
    median_minutes, max_gap_minutes = _compute_resolution_minutes(df)
    return WindDataSummary(
        station=station,
        rows=len(df),
        missing_speed=int(speed.isna().sum()),
        missing_dir=int(direction.isna().sum()),
        median_minutes=median_minutes,
        max_gap_minutes=max_gap_minutes,
        speed_unit=speed_unit,
    )


def _print_summary(summary: WindDataSummary) -> None:
    print(f"Station: {summary.station}")
    print(f"Rows: {summary.rows}")
    print(f"Missing wind speed: {summary.missing_speed}")
    print(f"Missing wind direction: {summary.missing_dir}")
    print(f"Median time step (minutes): {summary.median_minutes}")
    print(f"Max time gap (minutes): {summary.max_gap_minutes}")
    print(f"Wind speed unit: {summary.speed_unit}")

    if summary.median_minutes is None:
        print("Resolution check: insufficient data")
    elif summary.median_minutes <= 60:
        print("Resolution check: OK for hourly or higher CFD comparison")
    else:
        print("Resolution check: coarse, review before CFD comparison")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch ASOS wind data and validate temporal resolution."
    )
    parser.add_argument("--station", required=True, help="ASOS station ID, e.g. KJFK")
    parser.add_argument("--start", required=True, help="Start UTC time, YYYY-MM-DD HH:MM")
    parser.add_argument("--end", required=True, help="End UTC time, YYYY-MM-DD HH:MM")
    parser.add_argument("--out", help="Optional path to save CSV")
    args = parser.parse_args()

    start = _parse_time(args.start)
    end = _parse_time(args.end)
    if end <= start:
        raise SystemExit("End time must be after start time")

    df = fetch_wind_data(args.station, start, end)
    summary = validate_wind_data(df, args.station)
    _print_summary(summary)

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Saved CSV to {args.out}")


if __name__ == "__main__":
    main()

