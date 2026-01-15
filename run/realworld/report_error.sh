#!/usr/bin/env bash
set -euo pipefail

CASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_CSV="/home/bohanzhang/DroneWISP/python/realworld/nyc_100m_1km_cluster_wind.csv"
STID="0512W"
TIMESTAMP="2026-01-09T17:30:00Z"

CASE_DIR="$CASE_DIR" DATA_CSV="$DATA_CSV" STID="$STID" TIMESTAMP="$TIMESTAMP" \
  python3 "$CASE_DIR/report_error.py"

