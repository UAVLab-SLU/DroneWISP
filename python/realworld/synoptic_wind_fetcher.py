#!/usr/bin/env python3
"""
Fetch wind time series from Synoptic and validate temporal resolution.
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests


SYNOPTIC_TIMESERIES_URL = "https://api.synopticdata.com/v2/stations/timeseries"


@dataclass
class WindSummary:
    stid: str
    rows: int
    missing_speed: int
    missing_dir: int
    median_minutes: Optional[float]
    max_gap_minutes: Optional[float]
    speed_key: str
    dir_key: str


def _parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def _select_obs_keys(obs: Dict[str, List]) -> Tuple[Optional[str], Optional[str]]:
    speed_key = None
    dir_key = None
    for key in obs.keys():
        if key.startswith("wind_speed"):
            speed_key = key
        if key.startswith("wind_direction"):
            dir_key = key
    return speed_key, dir_key


def _compute_resolution_minutes(times: pd.Series) -> Tuple[Optional[float], Optional[float]]:
    times = pd.to_datetime(times, errors="coerce").dropna().sort_values()
    if len(times) < 2:
        return None, None
    deltas = times.diff().dropna().dt.total_seconds() / 60.0
    if deltas.empty:
        return None, None
    return float(deltas.median()), float(deltas.max())


def fetch_timeseries(
    token: str, stids: List[str], start: datetime, end: datetime, timeout: int = 30
) -> dict:
    params = {
        "token": token,
        "stid": ",".join(stids),
        "start": start.strftime("%Y%m%d%H%M"),
        "end": end.strftime("%Y%m%d%H%M"),
        "vars": "wind_speed,wind_direction",
        "units": "metric",
    }
    response = requests.get(SYNOPTIC_TIMESERIES_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    summary = payload.get("SUMMARY", {})
    if summary.get("RESPONSE_CODE") != 1:
        raise RuntimeError(f"Synoptic error: {summary}")
    return payload


def build_dataframe(payload: dict) -> pd.DataFrame:
    rows = []
    for station in payload.get("STATION", []):
        stid = station.get("STID", "")
        name = station.get("NAME", "")
        lat = station.get("LATITUDE")
        lon = station.get("LONGITUDE")
        obs = station.get("OBSERVATIONS", {})
        if "date_time" not in obs:
            continue
        speed_key, dir_key = _select_obs_keys(obs)
        if not speed_key or not dir_key:
            print(f"Skipping {stid}, missing wind keys: {list(obs.keys())}")
            continue
        for ts, speed, direction in zip(
            obs.get("date_time", []), obs.get(speed_key, []), obs.get(dir_key, [])
        ):
            rows.append(
                {
                    "stid": stid,
                    "name": name,
                    "lat": lat,
                    "lon": lon,
                    "date_time": ts,
                    "wind_speed": speed,
                    "wind_direction": direction,
                }
            )
    return pd.DataFrame(rows)


def summarize_station(df: pd.DataFrame, stid: str) -> WindSummary:
    df_station = df[df["stid"] == stid]
    times = df_station["date_time"]
    median_minutes, max_gap_minutes = _compute_resolution_minutes(times)
    return WindSummary(
        stid=stid,
        rows=len(df_station),
        missing_speed=int(df_station["wind_speed"].isna().sum()),
        missing_dir=int(df_station["wind_direction"].isna().sum()),
        median_minutes=median_minutes,
        max_gap_minutes=max_gap_minutes,
        speed_key="wind_speed",
        dir_key="wind_direction",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch Synoptic wind time series and validate resolution."
    )
    parser.add_argument("--stids", required=True, help="Comma-separated station IDs")
    parser.add_argument("--start", required=True, help="Start UTC time, YYYY-MM-DD HH:MM")
    parser.add_argument("--end", required=True, help="End UTC time, YYYY-MM-DD HH:MM")
    parser.add_argument("--out", help="Optional path to save combined CSV")
    parser.add_argument("--token", help="Synoptic token or set SYNOPTIC_TOKEN")
    args = parser.parse_args()

    token = args.token or os.environ.get("SYNOPTIC_TOKEN")
    if not token:
        raise SystemExit("Provide --token or set SYNOPTIC_TOKEN")

    stids = [s.strip() for s in args.stids.split(",") if s.strip()]
    start = _parse_time(args.start)
    end = _parse_time(args.end)
    if end <= start:
        raise SystemExit("End time must be after start time")

    payload = fetch_timeseries(token, stids, start, end)
    df = build_dataframe(payload)

    if df.empty:
        raise SystemExit("No wind data returned for the requested stations")

    for stid in sorted(set(df["stid"].tolist())):
        summary = summarize_station(df, stid)
        print(
            f"{summary.stid}: rows={summary.rows}, missing_speed={summary.missing_speed}, "
            f"missing_dir={summary.missing_dir}, median_min={summary.median_minutes}, "
            f"max_gap_min={summary.max_gap_minutes}"
        )

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Saved CSV to {args.out}")


if __name__ == "__main__":
    main()

