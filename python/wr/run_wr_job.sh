#!/usr/bin/env bash
set -euo pipefail

: "${WR_INPUT_STL_DIR:?WR_INPUT_STL_DIR is required}"
: "${WR_INPUT_STL_FILE:?WR_INPUT_STL_FILE is required}"
: "${WR_INPUT_CONFIG_DIR:?WR_INPUT_CONFIG_DIR is required}"
: "${WR_INPUT_CONFIG_FILE:?WR_INPUT_CONFIG_FILE is required}"
: "${WR_OUTPUT_DIR:?WR_OUTPUT_DIR is required}"
: "${WR_OUTPUT_FILE:?WR_OUTPUT_FILE is required}"

export WR_INPUT_STL_PATH="/wr/input/${WR_INPUT_STL_FILE}"
export WR_INPUT_CONFIG_PATH="/wr/config/${WR_INPUT_CONFIG_FILE}"
export WR_OUTPUT_CSV_PATH="/wr/output/${WR_OUTPUT_FILE}"

cd /home/wisp
exec python3 wr_batch_runner.py
