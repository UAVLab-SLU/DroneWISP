#!/bin/bash
# Clean all performance comparison cases

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Cleaning all cases..."

for CASE in fine_uniform coarse_local_wake; do
    if [ -d "$CASE" ]; then
        cd "$CASE"
        bash ./Allclean
        cd ..
        echo "Cleaned $CASE"
    fi
done

echo "All cases cleaned."
