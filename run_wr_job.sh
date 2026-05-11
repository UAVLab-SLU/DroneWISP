#!/usr/bin/env bash
set -euo pipefail

STL_PATH=""
CONFIG_PATH=""
OUTPUT_CSV=""
COMPOSE_FILE="compose.workflow-runner.yaml"

usage() {
  cat <<'EOF'
Usage:
  bash run_wr_job.sh --stl /path/to/terrain.stl --config /path/to/sim_config.json --output /path/to/result.csv

Options:
  --stl PATH
  --config PATH
  --output PATH
  --compose-file PATH
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stl)
      STL_PATH="$2"
      shift 2
      ;;
    --config)
      CONFIG_PATH="$2"
      shift 2
      ;;
    --output)
      OUTPUT_CSV="$2"
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

if [[ -z "$STL_PATH" || -z "$CONFIG_PATH" || -z "$OUTPUT_CSV" ]]; then
  echo "--stl, --config, and --output are required." >&2
  usage
  exit 1
fi

INPUT_STL_DIR="$(cd "$(dirname "$STL_PATH")" && pwd)"
INPUT_STL_FILE="$(basename "$STL_PATH")"
INPUT_CONFIG_DIR="$(cd "$(dirname "$CONFIG_PATH")" && pwd)"
INPUT_CONFIG_FILE="$(basename "$CONFIG_PATH")"
mkdir -p "$(dirname "$OUTPUT_CSV")"
OUTPUT_DIR="$(cd "$(dirname "$OUTPUT_CSV")" && pwd)"
OUTPUT_FILE="$(basename "$OUTPUT_CSV")"

export WR_INPUT_STL_DIR="$INPUT_STL_DIR"
export WR_INPUT_STL_FILE="$INPUT_STL_FILE"
export WR_INPUT_CONFIG_DIR="$INPUT_CONFIG_DIR"
export WR_INPUT_CONFIG_FILE="$INPUT_CONFIG_FILE"
export WR_OUTPUT_DIR="$OUTPUT_DIR"
export WR_OUTPUT_FILE="$OUTPUT_FILE"

docker compose -f "$COMPOSE_FILE" run --build --rm wisp_wr_job
