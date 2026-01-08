#!/bin/bash
# Wrapper script to run analyze_drone_model.py with the virtual environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/../../python/venv/bin/python3"

if [ ! -f "$VENV_PYTHON" ]; then
    echo "Error: Virtual environment not found at $VENV_PYTHON"
    echo "Please ensure the venv is set up in python/venv/"
    exit 1
fi

# Run the script with venv Python
exec "$VENV_PYTHON" "$SCRIPT_DIR/analyze_drone_model.py" "$@"

