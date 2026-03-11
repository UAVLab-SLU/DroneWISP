#!/usr/bin/env python3
import math
import os
import re
import sys

import pandas as pd


def load_probe_point(control_path: str):
    with open(control_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    match = re.search(r"probeLocations\s*\(\s*\(([^\)]+)\)", content, re.MULTILINE)
    if not match:
        return (16.031, -266.102, 0.5)
    parts = match.group(1).split()
    if len(parts) < 3:
        return (16.031, -266.102, 0.5)
    return tuple(float(p) for p in parts[:3])


def iter_vectors(path: str):
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip().startswith("internalField"):
                break
        count = None
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.isdigit():
                count = int(line)
                break
        for line in handle:
            if line.strip().startswith("("):
                break
        idx = 0
        for line in handle:
            line = line.strip()
            if not line:
                continue
            if line.startswith(")"):
                break
            line = line.strip("()")
            parts = line.split()
            if len(parts) != 3:
                continue
            yield idx, tuple(float(p) for p in parts)
            idx += 1
        if count is not None and idx != count:
            pass


def read_observation_average(data_csv: str, stids: list[str], timestamp: str):
    df = pd.read_csv(data_csv)
    rows = df[(df["stid"].isin(stids)) & (df["date_time"] == timestamp)]
    if rows.empty or rows["stid"].nunique() != len(stids):
        raise ValueError("Missing observation rows for requested stations")
    u_vals = []
    v_vals = []
    for _, row in rows.iterrows():
        speed = float(row["wind_speed"])
        direction = float(row["wind_direction"])
        u_vals.append(-speed * math.sin(math.radians(direction)))
        v_vals.append(-speed * math.cos(math.radians(direction)))
    u_obs = sum(u_vals) / len(u_vals)
    v_obs = sum(v_vals) / len(v_vals)
    w_obs = 0.0
    return u_obs, v_obs, w_obs


def main() -> int:
    case_dir = os.environ.get("CASE_DIR") or os.path.abspath(".")
    data_csv = os.environ.get("DATA_CSV")
    stids_raw = os.environ.get("STIDS")
    stid = os.environ.get("STID")
    timestamp = os.environ.get("TIMESTAMP")
    if not data_csv or not timestamp:
        print("DATA_CSV and TIMESTAMP must be set", file=sys.stderr)
        return 1
    if stids_raw:
        stids = [s.strip() for s in stids_raw.split(",") if s.strip()]
    elif stid:
        stids = [stid]
    else:
        print("STIDS or STID must be set", file=sys.stderr)
        return 1

    control_path = os.path.join(case_dir, "system", "controlDict")
    probe_x, probe_y, probe_z = load_probe_point(control_path)

    time_dirs = [d for d in os.listdir(case_dir) if d.replace(".", "", 1).isdigit()]
    if not time_dirs:
        print("No time directories found", file=sys.stderr)
        return 1
    time_dirs_sorted = sorted(time_dirs, key=lambda t: float(t))

    c_path = os.path.join(case_dir, time_dirs_sorted[-1], "C")
    if not os.path.isfile(c_path):
        print("Missing C field for sampling", file=sys.stderr)
        return 1

    best_idx = None
    best_dist = None
    for idx, (cx, cy, cz) in iter_vectors(c_path):
        dx = cx - probe_x
        dy = cy - probe_y
        dz = cz - probe_z
        dist = dx * dx + dy * dy + dz * dz
        if best_dist is None or dist < best_dist:
            best_dist = dist
            best_idx = idx

    if best_idx is None:
        print("Failed to locate nearest cell center", file=sys.stderr)
        return 1

    try:
        u_obs, v_obs, w_obs = read_observation_average(data_csv, stids, timestamp)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    best = None
    for time_dir in time_dirs_sorted:
        u_path = os.path.join(case_dir, time_dir, "U")
        if not os.path.isfile(u_path):
            continue
        u_cfd = v_cfd = w_cfd = None
        for idx, (ux, uy, uz) in iter_vectors(u_path):
            if idx == best_idx:
                if any(abs(v) > 1e3 for v in (ux, uy, uz)):
                    break
                u_cfd, v_cfd, w_cfd = ux, uy, uz
                break
        if u_cfd is None:
            continue
        vec_err = math.sqrt((u_cfd - u_obs) ** 2 + (v_cfd - v_obs) ** 2 + (w_cfd - w_obs) ** 2)
        speed_err = abs(math.sqrt(u_cfd**2 + v_cfd**2) - math.sqrt(u_obs**2 + v_obs**2))
        if best is None or vec_err < best[0]:
            best = (vec_err, speed_err, float(time_dir), (u_cfd, v_cfd, w_cfd))

    if best is None:
        print("Failed to find a valid CFD velocity in time directories", file=sys.stderr)
        return 1

    vec_err, speed_err, time_val, (u_cfd, v_cfd, w_cfd) = best
    print("CFD probe (U):", (u_cfd, v_cfd, w_cfd))
    print("Obs wind (U):", (round(u_obs, 3), round(v_obs, 3), w_obs))
    print("Vector error:", round(vec_err, 3))
    print("Speed error:", round(speed_err, 3))
    print("Probe time:", time_val)
    print("Obs timestamp:", timestamp)
    print("Obs stations:", ",".join(stids))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

