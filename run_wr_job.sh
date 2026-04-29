#!/usr/bin/env bash
set -euo pipefail

STL_PATH=""
OUTPUT_CSV=""
WIND_JSON=""
WIND_FILE=""
DIRECTION_CONVENTION="to"
CONTROL_JSON=""
BOUNDS_JSON=""
MESH_PADDING_JSON=""
FILL_MISSING="false"
COMPOSE_FILE="compose.workflow-runner.yaml"

usage() {
  cat <<'EOF'
Usage:
  bash run_wr_job.sh --stl /path/to/terrain.stl --output /path/to/result.csv --wind-file /path/to/sim_config.json

Options:
  --stl PATH
  --output PATH
  --wind-json JSON
  --wind-file PATH
  --direction-convention to|from
  --control-json JSON
  --bounds-json JSON
  --mesh-padding-json JSON
  --fill-missing true|false
  --compose-file PATH
EOF
}

extract_wind_json() {
  python3 - "$1" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text())
if isinstance(payload, dict):
    if isinstance(payload.get("environment"), dict) and "wind" in payload["environment"]:
        payload = payload["environment"]["wind"]
    elif "wind" in payload:
        payload = payload["wind"]
print(json.dumps(payload, separators=(",", ":")))
PY
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stl)
      STL_PATH="$2"
      shift 2
      ;;
    --output)
      OUTPUT_CSV="$2"
      shift 2
      ;;
    --wind-json)
      WIND_JSON="$2"
      shift 2
      ;;
    --wind-file)
      WIND_FILE="$2"
      shift 2
      ;;
    --direction-convention)
      DIRECTION_CONVENTION="$2"
      shift 2
      ;;
    --control-json)
      CONTROL_JSON="$2"
      shift 2
      ;;
    --bounds-json)
      BOUNDS_JSON="$2"
      shift 2
      ;;
    --mesh-padding-json)
      MESH_PADDING_JSON="$2"
      shift 2
      ;;
    --fill-missing)
      FILL_MISSING="$2"
      shift 2
      ;;
    --compose-file)
      COMPOSE_FILE="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$STL_PATH" || -z "$OUTPUT_CSV" ]]; then
  echo "--stl and --output are required." >&2
  usage
  exit 1
fi

if [[ -n "$WIND_FILE" ]]; then
  WIND_JSON="$(extract_wind_json "$WIND_FILE")"
fi

if [[ -z "$WIND_JSON" ]]; then
  echo "Provide either --wind-json or --wind-file." >&2
  usage
  exit 1
fi

INPUT_STL_DIR="$(cd "$(dirname "$STL_PATH")" && pwd)"
INPUT_STL_FILE="$(basename "$STL_PATH")"
mkdir -p "$(dirname "$OUTPUT_CSV")"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT_CSV")" && pwd)"
OUTPUT_FILE="$(basename "$OUTPUT_CSV")"

export WR_INPUT_STL_DIR="$INPUT_STL_DIR"
export WR_INPUT_STL_FILE="$INPUT_STL_FILE"
export WR_OUTPUT_DIR="$OUTPUT_DIR"
export WR_OUTPUT_FILE="$OUTPUT_FILE"
export WR_WIND_JSON="$WIND_JSON"
export WR_DIRECTION_CONVENTION="$DIRECTION_CONVENTION"
export WR_CONTROL_JSON="$CONTROL_JSON"
export WR_BOUNDS_JSON="$BOUNDS_JSON"
export WR_MESH_PADDING_JSON="$MESH_PADDING_JSON"
export WR_FILL_MISSING="$FILL_MISSING"

docker compose -f "$COMPOSE_FILE" run --build --rm wisp_wr_job
