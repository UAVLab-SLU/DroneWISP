#!/usr/bin/env python3
"""
Analyze wind CSV to find good multi-timestamp and multi-location candidate
scenarios for real-world validation (Reviewer 2, major #2).

Produces:
  1. Time-series plot of wind speed/direction for all stations on 2026-01-09
  2. Scatter plot of station-pair agreement (speed & direction similarity)
  3. Highlights the existing T0 (17:30) and chosen T1 (15:30) timestamps
  4. Identifies candidate timestamps where 2+ stations agree well
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np


CSV_PATH = Path(__file__).parent / "nyc_100m_1km_cluster_wind.csv"
OUT_DIR = Path(__file__).parent / "visualize"

STATIONS = ["0512W", "0514W", "0516W"]
STATION_LABELS = {
    "0512W": "0512W (South Campus)",
    "0514W": "0514W (Soccer Stadium)",
    "0516W": "0516W (Student Garden)",
}
STATION_COLORS = {"0512W": "#e41a1c", "0514W": "#377eb8", "0516W": "#4daf4a"}

# Existing and chosen timestamps
T0 = "2026-01-09T17:30:00Z"
T1 = "2026-01-09T15:30:00Z"

TARGET_DATE = "2026-01-09"


def angular_diff(a: float, b: float) -> float:
    """Smallest unsigned angle between two compass bearings (degrees)."""
    d = abs(a - b) % 360
    return d if d <= 180 else 360 - d


def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH)
    df["date_time"] = pd.to_datetime(df["date_time"])
    return df


def filter_day(df: pd.DataFrame, date_str: str) -> pd.DataFrame:
    day = pd.Timestamp(date_str)
    mask = (df["date_time"].dt.date == day.date()) & df["stid"].isin(STATIONS)
    return df[mask].copy()


def plot_timeseries(df_day: pd.DataFrame) -> None:
    """Plot wind speed and direction time series for all stations on the target day."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)

    for stid in STATIONS:
        sub = df_day[df_day["stid"] == stid].sort_values("date_time")
        ax1.plot(
            sub["date_time"],
            sub["wind_speed"],
            label=STATION_LABELS[stid],
            color=STATION_COLORS[stid],
            marker=".",
            markersize=3,
            linewidth=1,
        )
        ax2.scatter(
            sub["date_time"],
            sub["wind_direction"],
            label=STATION_LABELS[stid],
            color=STATION_COLORS[stid],
            s=10,
            alpha=0.7,
        )

    # Mark T0 and T1
    for ts, label, ls in [(T0, "T0 (17:30)", "--"), (T1, "T1 (15:30)", ":")]:
        t = pd.Timestamp(ts)
        ax1.axvline(t, color="gray", linestyle=ls, linewidth=1.5, alpha=0.8)
        ax2.axvline(t, color="gray", linestyle=ls, linewidth=1.5, alpha=0.8)
        ax1.text(
            t, ax1.get_ylim()[1] * 0.95, label,
            fontsize=8, ha="center", va="top",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.8),
        )

    ax1.set_ylabel("Wind Speed (m/s)")
    ax1.set_title(f"Wind Observations on {TARGET_DATE} — All Three Stations")
    ax1.legend(loc="upper left", fontsize=8)
    ax1.grid(True, alpha=0.3)

    ax2.set_ylabel("Wind Direction (°)")
    ax2.set_xlabel("Time (UTC)")
    ax2.set_ylim(0, 360)
    ax2.set_yticks(range(0, 361, 45))
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(True, alpha=0.3)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))

    fig.tight_layout()
    OUT_DIR.mkdir(exist_ok=True)
    fig.savefig(OUT_DIR / "multi_timestamp_timeseries.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_DIR / 'multi_timestamp_timeseries.png'}")


def compute_pairwise_agreement(df_day: pd.DataFrame) -> pd.DataFrame:
    """For each timestamp, compute pairwise station agreement metrics."""
    pairs = [("0512W", "0514W"), ("0512W", "0516W"), ("0514W", "0516W")]
    rows = []

    timestamps = sorted(df_day["date_time"].unique())
    for ts in timestamps:
        snapshot = df_day[df_day["date_time"] == ts]
        if len(snapshot) < 2:
            continue

        data = {}
        for _, row in snapshot.iterrows():
            data[row["stid"]] = (row["wind_speed"], row["wind_direction"])

        for s1, s2 in pairs:
            if s1 not in data or s2 not in data:
                continue
            sp1, d1 = data[s1]
            sp2, d2 = data[s2]

            # Skip if either has zero wind
            if sp1 == 0 or sp2 == 0:
                continue

            speed_ratio = min(sp1, sp2) / max(sp1, sp2)
            dir_diff = angular_diff(d1, d2)

            rows.append({
                "date_time": ts,
                "pair": f"{s1}-{s2}",
                "speed_1": sp1,
                "speed_2": sp2,
                "dir_1": d1,
                "dir_2": d2,
                "speed_ratio": speed_ratio,
                "dir_diff": dir_diff,
                "avg_speed": (sp1 + sp2) / 2,
            })

    return pd.DataFrame(rows)


def plot_pairwise_agreement(agreement: pd.DataFrame) -> None:
    """Plot pairwise station agreement: speed ratio vs direction difference."""
    pair_colors = {
        "0512W-0514W": "#e41a1c",
        "0512W-0516W": "#377eb8",
        "0514W-0516W": "#4daf4a",
    }

    fig, ax = plt.subplots(figsize=(10, 7))

    for pair_name, color in pair_colors.items():
        sub = agreement[agreement["pair"] == pair_name]
        sc = ax.scatter(
            sub["dir_diff"],
            sub["speed_ratio"],
            c=color,
            s=sub["avg_speed"] * 8,
            alpha=0.5,
            label=pair_name,
            edgecolors="white",
            linewidths=0.3,
        )

    # Highlight "good agreement" zone: dir_diff < 30° and speed_ratio > 0.6
    ax.axhline(0.6, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
    ax.axvline(30, color="gray", linestyle="--", alpha=0.5, linewidth=0.8)
    ax.fill_between([0, 30], 0.6, 1.0, color="green", alpha=0.08)
    ax.text(
        15, 0.95, "Good agreement\n(dir < 30°, ratio > 0.6)",
        ha="center", va="top", fontsize=9, color="green", alpha=0.8,
    )

    # Mark T0 and T1
    for ts_str, marker_label, marker_shape in [(T0, "T0", "^"), (T1, "T1", "s")]:
        ts = pd.Timestamp(ts_str)
        t_rows = agreement[agreement["date_time"] == ts]
        if not t_rows.empty:
            ax.scatter(
                t_rows["dir_diff"],
                t_rows["speed_ratio"],
                marker=marker_shape,
                s=120,
                c="black",
                zorder=5,
                label=f"{marker_label} ({ts_str[11:16]})",
                edgecolors="gold",
                linewidths=2,
            )

    ax.set_xlabel("Direction Difference Between Stations (°)")
    ax.set_ylabel("Speed Ratio (min/max)")
    ax.set_title(f"Station-Pair Wind Agreement — {TARGET_DATE}\n(marker size ∝ avg wind speed)")
    ax.set_xlim(0, 180)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower left", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "multi_location_pair_agreement.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_DIR / 'multi_location_pair_agreement.png'}")


def find_best_candidates(agreement: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Find timestamps with best multi-station agreement."""
    # Score: high speed_ratio + low dir_diff + high avg_speed
    ag = agreement.copy()
    ag["score"] = ag["speed_ratio"] * (1 - ag["dir_diff"] / 180) * ag["avg_speed"]

    # Group by timestamp, require at least 2 pairs with decent agreement
    grouped = ag.groupby("date_time").agg(
        n_pairs=("pair", "count"),
        mean_speed_ratio=("speed_ratio", "mean"),
        mean_dir_diff=("dir_diff", "mean"),
        mean_avg_speed=("avg_speed", "mean"),
        total_score=("score", "sum"),
    ).reset_index()

    grouped = grouped[grouped["n_pairs"] >= 2]
    grouped = grouped.sort_values("total_score", ascending=False)

    return grouped.head(top_n)


def plot_best_candidates(candidates: pd.DataFrame, agreement: pd.DataFrame) -> None:
    """Plot the top candidate timestamps with their station data."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))

    # Bar chart of candidate scores
    ax1 = axes[0]
    times = [t.strftime("%H:%M") for t in candidates["date_time"]]
    ax1.barh(
        range(len(candidates)),
        candidates["total_score"],
        color="#4daf4a",
        alpha=0.7,
    )
    ax1.set_yticks(range(len(candidates)))
    ax1.set_yticklabels(times)
    ax1.set_xlabel("Agreement Score")
    ax1.set_title(f"Top {len(candidates)} Candidate Timestamps for Multi-Station Validation")
    ax1.invert_yaxis()
    ax1.grid(True, alpha=0.3, axis="x")

    # Annotate with details
    for i, (_, row) in enumerate(candidates.iterrows()):
        ax1.text(
            row["total_score"] + 0.1,
            i,
            f"pairs={row['n_pairs']:.0f}, "
            f"spd_ratio={row['mean_speed_ratio']:.2f}, "
            f"dir_diff={row['mean_dir_diff']:.0f}°, "
            f"avg_spd={row['mean_avg_speed']:.1f} m/s",
            va="center",
            fontsize=8,
        )

    # Table of detailed station data for top 5
    ax2 = axes[1]
    ax2.axis("off")
    top5 = candidates.head(5)
    table_data = []
    headers = ["Time", "0512W spd/dir", "0514W spd/dir", "0516W spd/dir", "Score"]

    for _, row in top5.iterrows():
        ts = row["date_time"]
        time_str = ts.strftime("%H:%M")
        # Get individual station data
        cells = [time_str]
        for stid in STATIONS:
            pairs = agreement[
                (agreement["date_time"] == ts)
                & (agreement["pair"].str.contains(stid))
            ]
            if not pairs.empty:
                first = pairs.iloc[0]
                if first["pair"].startswith(stid):
                    spd, d = first["speed_1"], first["dir_1"]
                else:
                    spd, d = first["speed_2"], first["dir_2"]
                cells.append(f"{spd:.1f} / {d:.0f}°")
            else:
                cells.append("—")
        cells.append(f"{row['total_score']:.2f}")
        table_data.append(cells)

    table = ax2.table(
        cellText=table_data,
        colLabels=headers,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1.0, 1.6)
    ax2.set_title("Top 5 Candidate Timestamps — Station Details", fontsize=11, pad=10)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "multi_scenario_candidates.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {OUT_DIR / 'multi_scenario_candidates.png'}")


def main() -> None:
    df = load_data()
    df_day = filter_day(df, TARGET_DATE)

    print(f"Data for {TARGET_DATE}: {len(df_day)} rows across {df_day['stid'].nunique()} stations")
    print(f"Stations: {', '.join(df_day['stid'].unique())}")

    # 1. Time-series plot
    plot_timeseries(df_day)

    # 2. Pairwise agreement analysis
    agreement = compute_pairwise_agreement(df_day)
    print(f"\nPairwise comparisons: {len(agreement)}")

    plot_pairwise_agreement(agreement)

    # 3. Find and plot best candidates
    candidates = find_best_candidates(agreement, top_n=10)
    print("\n--- Top 10 multi-station agreement timestamps ---")
    for _, row in candidates.iterrows():
        print(
            f"  {row['date_time'].strftime('%H:%M')} | "
            f"pairs={row['n_pairs']:.0f} | "
            f"speed_ratio={row['mean_speed_ratio']:.2f} | "
            f"dir_diff={row['mean_dir_diff']:.0f}° | "
            f"avg_speed={row['mean_avg_speed']:.1f} m/s | "
            f"score={row['total_score']:.2f}"
        )

    plot_best_candidates(candidates, agreement)

    print("\n--- Reference timestamps ---")
    print(f"  T0 (existing):  {T0}  → 0512W: 7.151 m/s @ 167°")
    print(f"  T1 (new case):  {T1}  → 0512W: 6.703 m/s @ 149°")
    print("\nReview the plots in:", OUT_DIR)


if __name__ == "__main__":
    main()
